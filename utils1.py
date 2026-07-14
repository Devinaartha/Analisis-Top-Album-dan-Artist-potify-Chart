from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


REQUIRED_COLUMNS = [
    "date",
    "country",
    "rank",
    "album_name",
    "artist_names",
    "weeks_on_chart",
]


class DataProcessor:
    """Membaca, membersihkan, dan memfilter dataset Spotify chart."""

    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        self.raw_data = pd.DataFrame()
        self.cleaned_data = pd.DataFrame()
        self.missing_before = pd.Series(dtype="int64")
        self.missing_after = pd.Series(dtype="int64")

    def load_raw_data(self) -> pd.DataFrame:
        if not self.file_path.exists():
            raise FileNotFoundError(
                f"File dataset tidak ditemukan: {self.file_path}. "
                "Pastikan folder dataset berisi charts_albums_weekly.csv."
            )

        self.raw_data = pd.read_csv(self.file_path, usecols=REQUIRED_COLUMNS)
        if self.raw_data.empty:
            raise ValueError("Dataset ditemukan tetapi kosong.")

        self.missing_before = self.raw_data.isna().sum()
        return self.raw_data

    def clean_data(self) -> pd.DataFrame:
        if self.raw_data.empty:
            raise ValueError("Data mentah belum dimuat. Jalankan load_raw_data() terlebih dahulu.")

        df = self.raw_data.copy()
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["rank"] = pd.to_numeric(df["rank"], errors="coerce")
        df["weeks_on_chart"] = pd.to_numeric(df["weeks_on_chart"], errors="coerce")

        df = df.dropna(subset=["date", "country", "rank", "album_name", "artist_names"])
        df["album_name"] = df["album_name"].astype(str).str.strip()
        df["artist_names"] = df["artist_names"].astype(str).str.strip()
        df["country"] = df["country"].astype(str).str.lower().str.strip()
        df["rank"] = df["rank"].astype(int)
        df["chart_score"] = 201 - df["rank"]

        self.cleaned_data = df
        self.missing_after = self.cleaned_data[REQUIRED_COLUMNS].isna().sum()
        return self.cleaned_data

    def filter_by_country_and_date(self, country: str, start_date: str) -> pd.DataFrame:
        if self.cleaned_data.empty:
            raise ValueError("Data belum dibersihkan. Jalankan clean_data() terlebih dahulu.")

        try:
            target_date = pd.to_datetime(start_date)
        except ValueError as exception:
            raise ValueError("Format tanggal tidak valid. Gunakan format YYYY-MM-DD.") from exception

        normalized_country = country.lower().strip()
        is_target_country = self.cleaned_data["country"] == normalized_country
        is_after_start_date = self.cleaned_data["date"] >= target_date
        return self.cleaned_data.loc[is_target_country & is_after_start_date].copy()


class DataAnalyzer:
    """Menghitung metrik top album, top artis, dan heatmap bulanan."""

    def __init__(self, data: pd.DataFrame):
        if data.empty:
            raise ValueError("Data analisis kosong.")
        self.data = data

    def get_top_albums(self, top_n: int = 10) -> pd.DataFrame:
        top_albums = (
            self.data.groupby(["album_name", "artist_names"], as_index=False)
            .agg(
                total_chart_score=("chart_score", "sum"),
                appearances=("date", "count"),
                best_rank=("rank", "min"),
                average_rank=("rank", "mean"),
                max_weeks_on_chart=("weeks_on_chart", "max"),
            )
            .sort_values(
                by=["total_chart_score", "appearances", "best_rank"],
                ascending=[False, False, True],
            )
            .head(top_n)
        )
        top_albums["average_rank"] = top_albums["average_rank"].round(2)
        return top_albums

    def get_top_artists(self, top_n: int = 10) -> pd.DataFrame:
        top_artists = (
            self.data.groupby("artist_names", as_index=False)
            .agg(
                total_chart_score=("chart_score", "sum"),
                chart_entries=("album_name", "count"),
                unique_albums=("album_name", "nunique"),
                best_rank=("rank", "min"),
                average_rank=("rank", "mean"),
            )
            .sort_values(
                by=["total_chart_score", "chart_entries", "best_rank"],
                ascending=[False, False, True],
            )
            .head(top_n)
        )
        top_artists["average_rank"] = top_artists["average_rank"].round(2)
        return top_artists

    def get_artist_monthly_heatmap(self, top_artists: pd.DataFrame) -> pd.DataFrame:
        top_artist_names = top_artists["artist_names"].tolist()
        heatmap_data = self.data[self.data["artist_names"].isin(top_artist_names)].copy()
        heatmap_data["month"] = heatmap_data["date"].dt.to_period("M").astype(str)

        return (
            heatmap_data.groupby(["artist_names", "month"])["chart_score"]
            .sum()
            .unstack(fill_value=0)
            .reindex(top_artist_names)
        )


class ReportGenerator:
    """Membuat laporan teks dari hasil analisis."""

    def __init__(
        self,
        data: pd.DataFrame,
        top_albums: pd.DataFrame,
        top_artists: pd.DataFrame,
        missing_before: pd.Series | None = None,
        missing_after: pd.Series | None = None,
    ):
        self.data = data
        self.top_albums = top_albums
        self.top_artists = top_artists
        self.missing_before = missing_before
        self.missing_after = missing_after

    def build_summary_text(self, country: str, start_date: str) -> str:
        latest_date = self.data["date"].max().date()
        earliest_date = self.data["date"].min().date()

        lines = [
            "==========================================",
            "LAPORAN EKSEKUTIF: SPOTIFY CHART ANALYTICS",
            "==========================================",
            f"Negara            : {country.upper()}",
            f"Filter mulai      : {start_date}",
            f"Periode analisis  : {earliest_date} s/d {latest_date}",
            f"Total entri       : {len(self.data):,}",
            f"Total album unik  : {self.data['album_name'].nunique():,}",
            f"Total artis unik  : {self.data['artist_names'].nunique():,}",
            f"Rank terbaik      : {self.data['rank'].min()}",
            f"Rank terendah     : {self.data['rank'].max()}",
            "",
            "Catatan metode:",
            "Dataset berisi chart mingguan album, bukan jumlah stream langsung.",
            "Dominasi album/artis diperkirakan dengan chart_score = 201 - rank.",
            "",
            "10 ALBUM TERATAS",
            "------------------------------------------",
        ]

        for index, row in enumerate(self.top_albums.itertuples(index=False), start=1):
            lines.append(
                f"{index}. {row.album_name} ({row.artist_names}) | "
                f"score={row.total_chart_score:,}, appearances={row.appearances}, "
                f"best_rank={row.best_rank}, avg_rank={row.average_rank}"
            )

        lines.extend(["", "10 ARTIS TERATAS", "------------------------------------------"])
        for index, row in enumerate(self.top_artists.itertuples(index=False), start=1):
            lines.append(
                f"{index}. {row.artist_names} | score={row.total_chart_score:,}, "
                f"chart_entries={row.chart_entries}, unique_albums={row.unique_albums}, "
                f"best_rank={row.best_rank}, avg_rank={row.average_rank}"
            )

        if self.missing_before is not None or self.missing_after is not None:
            lines.extend(["", "MISSING VALUES", "------------------------------------------"])
            if self.missing_before is not None:
                lines.append("Sebelum cleaning:")
                lines.extend(self._format_missing_values(self.missing_before))
            if self.missing_after is not None:
                lines.append("Setelah cleaning:")
                lines.extend(self._format_missing_values(self.missing_after))

        return "\n".join(lines)

    @staticmethod
    def _format_missing_values(missing_values: pd.Series) -> list[str]:
        return [f"- {column}: {int(total):,}" for column, total in missing_values.items()]

    def save_to_file(self, summary_text: str, output_path: Path) -> None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(summary_text, encoding="utf-8")


class Visualizer:
    """Membuat grafik dan dashboard ringkasan dengan Matplotlib."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._configure_default_styles()

    def _configure_default_styles(self) -> None:
        plt.rcParams["font.family"] = "sans-serif"
        plt.rcParams["axes.titlesize"] = 14
        plt.rcParams["axes.titleweight"] = "normal"

    def _remove_top_and_right_borders(self, axis: plt.Axes) -> None:
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.spines["left"].set_color("#dddddd")
        axis.spines["bottom"].set_color("#dddddd")

    def _save_and_close_figure(self, filename: str) -> None:
        plt.tight_layout()
        plt.show()
        plt.savefig(self.output_dir / filename, dpi=160, bbox_inches="tight")
        plt.close()

    def plot_top_albums(self, top_albums: pd.DataFrame, filename: str) -> None:
        labels = top_albums["album_name"] + " - " + top_albums["artist_names"]
        _, ax = plt.subplots(figsize=(12, 7))
        bars = ax.barh(labels[::-1], top_albums["total_chart_score"][::-1], color="#3498db")

        ax.set_title("Top 10 Album Chart Indonesia Sejak 2025", pad=15)
        ax.set_xlabel("Total Poin", color="#555555")
        self._remove_top_and_right_borders(ax)
        ax.grid(axis="x", linestyle="--", alpha=0.4)
        ax.bar_label(bars, fmt="%d", padding=5, color="#333333", fontsize=10)
        self._save_and_close_figure(filename)

    def plot_top_artists(self, top_artists: pd.DataFrame, filename: str) -> None:
        _, ax = plt.subplots(figsize=(12, 6))
        bars = ax.bar(top_artists["artist_names"], top_artists["total_chart_score"], color="#2ecc71")

        ax.set_title("Top 10 Artist Chart Indonesia Sejak 2025", pad=15)
        ax.set_ylabel("Total Poin", color="#555555")
        plt.xticks(rotation=40, ha="right")
        self._remove_top_and_right_borders(ax)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.bar_label(bars, fmt="%d", padding=3, color="#333333", fontsize=10)
        self._save_and_close_figure(filename)

    def plot_artist_monthly_heatmap(self, artist_month_score: pd.DataFrame, filename: str) -> None:
        fig, ax = plt.subplots(figsize=(13, 7))
        image = ax.imshow(artist_month_score.values, aspect="auto", cmap="YlGnBu")

        ax.set_title("Heatmap Total Chart Score Artist per Bulan", pad=15)
        ax.set_xticks(range(len(artist_month_score.columns)))
        ax.set_xticklabels(artist_month_score.columns, rotation=45, ha="right")
        ax.set_yticks(range(len(artist_month_score.index)))
        ax.set_yticklabels(artist_month_score.index)
        fig.colorbar(image, ax=ax, label="Total Skor")
        self._save_and_close_figure(filename)

    def plot_artist_rank_boxplot(self, df: pd.DataFrame, top_artists: pd.DataFrame, filename: str) -> None:
        top_artist_names = top_artists["artist_names"].tolist()
        boxplot_data = [df.loc[df["artist_names"] == artist_name, "rank"] for artist_name in top_artist_names]

        _, ax = plt.subplots(figsize=(13, 7))
        ax.boxplot(
            boxplot_data,
           tick_labels=top_artist_names,
            patch_artist=True,
            boxprops={"facecolor": "#ecf0f1", "color": "#7f8c8d"},
            medianprops={"color": "#e74c3c", "linewidth": 2},
        )

        ax.set_title("Box Plot Distribusi Rank Top Artist", pad=15)
        ax.set_ylabel("Peringkat (lebih kecil lebih baik)")
        plt.xticks(rotation=40, ha="right")
        self._remove_top_and_right_borders(ax)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.invert_yaxis()
        self._save_and_close_figure(filename)

    def plot_artist_score_pie(self, top_artists: pd.DataFrame, filename: str) -> None:
        _, ax = plt.subplots(figsize=(9, 8))
        color_palette = plt.cm.Set3(range(len(top_artists)))

        ax.pie(
            top_artists["total_chart_score"],
            labels=top_artists["artist_names"],
            autopct="%1.1f%%",
            startangle=140,
            colors=color_palette,
            wedgeprops={"edgecolor": "white", "linewidth": 1.5},
        )
        ax.set_title("Pie Chart Proporsi Total Chart Score Top 10 Artist")
        self._save_and_close_figure(filename)

    def plot_summary_dashboard(
        self,
        df: pd.DataFrame,
        top_albums: pd.DataFrame,
        top_artists: pd.DataFrame,
        filename: str,
    ) -> None:
        fig, axes = plt.subplots(2, 2, figsize=(16, 11))

        album_labels = top_albums["album_name"] + " - " + top_albums["artist_names"]
        axes[0, 0].barh(album_labels[::-1], top_albums["total_chart_score"][::-1], color="#3498db")
        axes[0, 0].set_title("Top 10 Album")
        self._remove_top_and_right_borders(axes[0, 0])
        axes[0, 0].grid(axis="x", linestyle="--", alpha=0.4)

        axes[0, 1].bar(top_artists["artist_names"], top_artists["total_chart_score"], color="#2ecc71")
        axes[0, 1].set_title("Top 10 Artist")
        axes[0, 1].tick_params(axis="x", rotation=40)
        self._remove_top_and_right_borders(axes[0, 1])
        axes[0, 1].grid(axis="y", linestyle="--", alpha=0.4)

        axes[1, 0].pie(
            top_artists["total_chart_score"],
            labels=top_artists["artist_names"],
            autopct="%1.1f%%",
            startangle=140,
            colors=plt.cm.Set3(range(len(top_artists))),
            wedgeprops={"edgecolor": "white", "linewidth": 1.5},
        )
        axes[1, 0].set_title("Proporsi Score Top Artist")

        axes[1, 1].scatter(df["weeks_on_chart"], df["rank"], alpha=0.4, color="#e67e22", edgecolors="none")
        axes[1, 1].invert_yaxis()
        axes[1, 1].set_title("Weeks on Chart vs Rank")
        axes[1, 1].set_xlabel("Total Minggu di Chart")
        axes[1, 1].set_ylabel("Peringkat (kecil = baik)")
        self._remove_top_and_right_borders(axes[1, 1])
        axes[1, 1].grid(linestyle="--", alpha=0.4)

        plt.subplots_adjust(bottom=0.05, hspace=0.3)
        self._save_and_close_figure(filename)
