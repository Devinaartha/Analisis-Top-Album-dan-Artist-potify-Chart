import argparse
import re
import sys
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Confirm, Prompt
except ModuleNotFoundError:
    class Console:
        def print(self, *objects, **kwargs) -> None:
            text = " ".join(str(item) for item in objects)
            print(re.sub(r"\[/?[^\]]+\]", "", text))

    class Panel:
        def __init__(self, renderable, title=None, **kwargs):
            self.renderable = renderable
            self.title = title

        def __str__(self) -> str:
            return f"{self.title}\n{self.renderable}" if self.title else str(self.renderable)

    class Progress:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def add_task(self, description, total=None):
            print(re.sub(r"\[/?[^\]]+\]", "", description))
            return 0

        def update(self, task_id, **kwargs) -> None:
            pass

        def stop(self) -> None:
            pass

    class SpinnerColumn:
        pass

    class TextColumn:
        def __init__(self, *args, **kwargs):
            pass

    class Prompt:
        @staticmethod
        def ask(prompt_text, default=None):
            suffix = f" [{default}]" if default is not None else ""
            value = input(f"{prompt_text}{suffix}: ").strip()
            return value or default or ""

    class Confirm:
        @staticmethod
        def ask(prompt_text, default=False):
            default_label = "y" if default else "n"
            value = input(f"{prompt_text} [y/n, default {default_label}]: ").strip().lower()
            if not value:
                return default
            return value in {"y", "yes", "ya"}

from utils1 import DataAnalyzer, DataProcessor, ReportGenerator, Visualizer


console = Console()

OUTPUT_FILES = {
    "report": "hasil_analisis.txt",
    "top_albums": "grafik_top10_album.png",
    "top_artists": "grafik_top10_artist.png",
    "heatmap": "grafik_heatmap_artist.png",
    "boxplot": "grafik_boxplot_rank.png",
    "pie_score": "grafik_pie_score.png",
    "dashboard": "grafik_dashboard.png",
}


class SpotifyDashboardApp:
    """Orchestrator utama untuk pemrosesan data, analisis, laporan, dan grafik."""

    def __init__(self, dataset_path: Path, output_dir: Path, country: str, start_date: str):
        self.dataset_path = dataset_path
        self.output_dir = output_dir
        self.country = country.lower().strip()
        self.start_date = start_date.strip()

        self._prepare_output_directory()

    def _prepare_output_directory(self) -> None:
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exception:
            raise RuntimeError(f"Tidak dapat membuat folder output: {exception}") from exception

    def run(self) -> bool:
        """Menjalankan seluruh alur program. Return False jika data tidak ditemukan."""
        self._print_header()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task1 = progress.add_task("[cyan]Membaca dan membersihkan data...", total=None)
            try:
                processor = DataProcessor(self.dataset_path)
                processor.load_raw_data()
                processor.clean_data()
                filtered_data = processor.filter_by_country_and_date(self.country, self.start_date)
            except Exception as exception:
                progress.stop()
                console.print(f"\n[bold red]GAGAL MEMPROSES DATA:[/bold red] {exception}")
                return False

            if filtered_data.empty:
                progress.stop()
                self._print_no_data_warning()
                return False

            progress.update(task1, completed=True)
            console.print("[green]OK[/green] Data berhasil dibaca dan disaring.")

            task2 = progress.add_task("[cyan]Menganalisis metrik statistik...", total=None)
            analyzer = DataAnalyzer(filtered_data)
            top_albums = analyzer.get_top_albums(top_n=10)
            top_artists = analyzer.get_top_artists(top_n=10)
            artist_monthly_heatmap = analyzer.get_artist_monthly_heatmap(top_artists)

            progress.update(task2, completed=True)
            console.print("[green]OK[/green] Analisis statistik selesai.")

            task3 = progress.add_task("[cyan]Menyusun laporan teks...", total=None)
            reporter = ReportGenerator(
                filtered_data,
                top_albums,
                top_artists,
                missing_before=processor.missing_before,
                missing_after=processor.missing_after,
            )
            summary_text = reporter.build_summary_text(self.country, self.start_date)
            reporter.save_to_file(summary_text, self.output_dir / OUTPUT_FILES["report"])

            progress.update(task3, completed=True)
            console.print("[green]OK[/green] Laporan teks berhasil disimpan.")

            task4 = progress.add_task("[cyan]Membuat visualisasi grafik...", total=None)
            try:
                visualizer = Visualizer(self.output_dir)
                visualizer.plot_top_albums(top_albums, OUTPUT_FILES["top_albums"])
                visualizer.plot_top_artists(top_artists, OUTPUT_FILES["top_artists"])
                visualizer.plot_artist_monthly_heatmap(artist_monthly_heatmap, OUTPUT_FILES["heatmap"])
                visualizer.plot_artist_rank_boxplot(filtered_data, top_artists, OUTPUT_FILES["boxplot"])
                visualizer.plot_artist_score_pie(top_artists, OUTPUT_FILES["pie_score"])
                visualizer.plot_summary_dashboard(filtered_data, top_albums, top_artists, OUTPUT_FILES["dashboard"])
            except Exception as exception:
                progress.stop()
                console.print(f"\n[bold red]GAGAL MEMBUAT VISUALISASI:[/bold red] {exception}")
                return False

            progress.update(task4, completed=True)
            console.print("[green]OK[/green] Visualisasi grafik berhasil dibuat.")

        self._print_footer()
        return True

    def _print_header(self) -> None:
        header_text = (
            f"Negara : [bold yellow]{self.country.upper()}[/bold yellow]\n"
            f"Sejak  : [bold yellow]{self.start_date}[/bold yellow]"
        )
        console.print(Panel(header_text, title="SPOTIFY CHART ANALYTICS", expand=False, border_style="green"))

    def _print_no_data_warning(self) -> None:
        console.print("\n[bold red]DATA TIDAK DITEMUKAN[/bold red]")
        console.print(
            f"Tidak ada data tangga lagu untuk negara [bold]{self.country.upper()}[/bold] "
            f"sejak [bold]{self.start_date}[/bold]."
        )
        console.print(
            Panel(
                "[bold]Tips:[/bold] Coba gunakan negara 'global' atau pastikan tanggal tidak melampaui data terbaru.",
                border_style="yellow",
                expand=False,
            )
        )

    def _print_footer(self) -> None:
        console.print("\n[bold green]ANALISIS SELESAI![/bold green]")
        output_path = self.output_dir.absolute()
        console.print(f"Hasil tersimpan di: [bold blue][link=file://{output_path}]{output_path}[/link][/bold blue]\n")


def get_valid_date(prompt_text: str, default_date: str) -> str:
    """Meminta input tanggal sampai formatnya sesuai YYYY-MM-DD."""
    while True:
        date_input = Prompt.ask(prompt_text, default=default_date).strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_input):
            return date_input
        console.print("[bold red]Format salah.[/bold red] Harap gunakan format YYYY-MM-DD (Contoh: 2024-01-01).")


def get_user_inputs(args: argparse.Namespace) -> tuple[str, str]:
    """Mengambil input dari argumen terminal atau mode interaktif."""
    if args.country and args.date:
        return args.country, args.date

    console.print("\n[dim]Argumen tidak lengkap. Memulai mode interaktif...[/dim]")
    country = Prompt.ask("Masukkan kode negara (contoh: id, us, jp, global)", default="id")
    date = get_valid_date("Masukkan tanggal mulai", "2024-01-01")
    return country, date


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analisis Tangga Lagu Spotify - laporan statistik dan grafik visual.",
        epilog="Contoh: py spotify_album_indonesia_project/main1.py --country id --date 2024-01-01",
    )
    parser.add_argument("-c", "--country", type=str, help="Kode negara (contoh: id, us, global).")
    parser.add_argument("-d", "--date", type=str, help="Tanggal mulai (YYYY-MM-DD).")
    args = parser.parse_args()

    project_dir = Path(__file__).resolve().parent
    csv_path = project_dir / "dataset" / "charts_albums_weekly.csv"
    output_dir = project_dir / "output_analisis"

    while True:
        country_input, date_input = get_user_inputs(args)

        try:
            app = SpotifyDashboardApp(
                dataset_path=csv_path,
                output_dir=output_dir,
                country=country_input,
                start_date=date_input,
            )
        except RuntimeError as exception:
            console.print(f"[bold red]GAGAL:[/bold red] {exception}")
            sys.exit(1)

        is_success = app.run()
        if is_success:
            break

        retry = Confirm.ask("\nIngin mencoba parameter pencarian lain?", default=False)
        if not retry:
            console.print("[dim]Keluar dari program.[/dim]")
            break

        args.country = None
        args.date = None


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[bold red]Operasi dibatalkan oleh pengguna.[/bold red]")
        sys.exit(0)
