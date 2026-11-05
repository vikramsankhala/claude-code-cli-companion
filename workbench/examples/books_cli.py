"""Chapter 39 example. Run: python books_cli.py --n 3"""
import typer
from rich.console import Console
from rich.table import Table
app = typer.Typer()

@app.command()
def books(n: int = 3):
    t = Table("Title", "Year")
    for i in range(n): t.add_row(f"Book {i+1}", "2026")
    Console().print(t)

if __name__ == "__main__": app()
