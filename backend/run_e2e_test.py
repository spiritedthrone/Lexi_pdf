"""End-to-end test: Upload → Extract → Chunk → Simplify → Merge → Download PDF."""
import asyncio
import time
import fitz
import httpx
from app.core.config import settings

BASE_URL = "http://127.0.0.1:8000/api/v1"


async def e2e_test():
    async with httpx.AsyncClient(timeout=90.0) as client:
        # 1. Upload
        with open("test_sample.pdf", "rb") as f:
            t0 = time.perf_counter()
            resp = await client.post(
                f"{BASE_URL}/upload/",
                files={"file": ("test_sample.pdf", f, "application/pdf")},
            )
            upload_dt = time.perf_counter() - t0
        assert resp.status_code == 201, f"Upload failed: {resp.text}"
        data = resp.json()
        file_id = data["id"]
        print(f"[1] Upload + Extract + Chunk  OK  {upload_dt:.3f}s | file_id={file_id}")
        print(f"    Pages: {data['page_count']}  Characters: {data['total_characters']}  Chunks: {data['chunk_count']}")

        # 2. Simplify
        t0 = time.perf_counter()
        resp = await client.post(f"{BASE_URL}/simplify/{file_id}")
        simplify_dt = time.perf_counter() - t0
        assert resp.status_code == 200, f"Simplify failed: {resp.text}"
        simp = resp.json()
        print(f"[2] Simplify + Merge          OK  {simplify_dt:.3f}s | Paragraphs={simp['total_paragraphs']}  Words={simp['total_words']}")
        print(f"    Sample: {simp['full_text'][:150]}...")

        # 3. Download PDF
        t0 = time.perf_counter()
        resp = await client.get(f"{BASE_URL}/simplify/{file_id}/download")
        dl_dt = time.perf_counter() - t0
        assert resp.status_code == 200, f"Download failed: {resp.text}"
        assert resp.headers["content-type"] == "application/pdf"

        doc = fitz.open(stream=resp.content, filetype="pdf")
        pages = len(doc)
        size = len(resp.content)
        text_snippet = doc[0].get_text()[:120]
        doc.close()

        print(f"[3] Generate + Download PDF   OK  {dl_dt:.3f}s | Pages={pages}  Size={size} bytes")
        print(f"    PDF snippet: {text_snippet}")

        total = upload_dt + simplify_dt + dl_dt
        print(f"\n=== TOTAL END-TO-END TIME: {total:.3f}s ===")
        print(f"Model used: Google Gemini API ({settings.active_model})")


asyncio.run(e2e_test())
