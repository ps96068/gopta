# services/dashboard/pdf_cleanup.py
"""
Utilitar pentru curățarea PDF-urilor orfane.
Poate fi rulat periodic pentru a șterge PDF-uri care nu mai au invoice în DB.
"""

import asyncio
from pathlib import Path
from typing import List, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cfg import get_db
from models import Invoice
from services.dashboard.pdf_service_reportlab import PDFService


class PDFCleanup:
    """Service pentru curățarea PDF-urilor orfane."""

    @staticmethod
    async def find_orphan_pdfs(db: AsyncSession) -> List[Tuple[Path, str]]:
        """
        Găsește PDF-uri care nu mai au invoice în baza de date.

        Returns:
            Lista de tuple (path, reason) pentru fișierele orfane
        """
        orphans = []
        pdf_dir = PDFService.OUTPUT_DIR

        if not pdf_dir.exists():
            return orphans

        # Obține toate path-urile din DB
        result = await db.execute(
            select(Invoice.document_path).where(Invoice.document_path.isnot(None))
        )
        db_paths = {Path(row[0]).name for row in result if row[0]}

        # Parcurge toate PDF-urile de pe disc
        for pdf_file in pdf_dir.rglob("*.pdf"):
            if pdf_file.name not in db_paths:
                orphans.append((pdf_file, "No database record"))

        return orphans

    @staticmethod
    async def cleanup_orphan_pdfs(db: AsyncSession, dry_run: bool = True) -> dict:
        """
        Curăță PDF-urile orfane.

        Args:
            db: Sesiunea de bază de date
            dry_run: Dacă True, doar raportează ce ar șterge fără să șteargă efectiv

        Returns:
            Dicționar cu statistici despre curățare
        """
        orphans = await PDFCleanup.find_orphan_pdfs(db)

        stats = {
            "found": len(orphans),
            "deleted": 0,
            "failed": 0,
            "total_size": 0,
            "files": []
        }

        for pdf_path, reason in orphans:
            file_info = {
                "path": str(pdf_path),
                "reason": reason,
                "size": pdf_path.stat().st_size if pdf_path.exists() else 0,
                "status": "pending"
            }

            stats["total_size"] += file_info["size"]

            if not dry_run:
                try:
                    pdf_path.unlink()
                    file_info["status"] = "deleted"
                    stats["deleted"] += 1

                    # Curăță directoarele goale
                    parent = pdf_path.parent
                    if parent.exists() and not any(parent.iterdir()):
                        parent.rmdir()

                except Exception as e:
                    file_info["status"] = f"failed: {str(e)}"
                    stats["failed"] += 1
            else:
                file_info["status"] = "would_delete"

            stats["files"].append(file_info)

        return stats


async def cleanup_pdfs_command(dry_run: bool = True):
    """
    Comandă pentru curățarea PDF-urilor orfane.
    Poate fi rulată din linia de comandă sau ca task periodic.
    """
    print(f"Starting PDF cleanup (dry_run={dry_run})...")

    async for db in get_db():
        try:
            stats = await PDFCleanup.cleanup_orphan_pdfs(db, dry_run=dry_run)

            print(f"\nCleanup Statistics:")
            print(f"- Found: {stats['found']} orphan PDFs")
            print(f"- Total size: {stats['total_size'] / 1024 / 1024:.2f} MB")

            if not dry_run:
                print(f"- Deleted: {stats['deleted']}")
                print(f"- Failed: {stats['failed']}")
            else:
                print("- This was a dry run. Use --no-dry-run to actually delete files.")

            if stats['files']:
                print("\nDetails:")
                for file in stats['files'][:10]:  # Show first 10
                    print(f"  - {file['path']}: {file['status']}")

                if len(stats['files']) > 10:
                    print(f"  ... and {len(stats['files']) - 10} more files")

        finally:
            await db.close()


if __name__ == "__main__":
    import sys

    dry_run = "--no-dry-run" not in sys.argv
    asyncio.run(cleanup_pdfs_command(dry_run=dry_run))