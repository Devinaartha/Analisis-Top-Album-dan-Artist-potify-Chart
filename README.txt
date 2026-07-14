Judul proyek: Analisis Top Album dan Artist Spotify Chart
Anggota kelompok 7:
Fadhil Muhammad Habibie		(25.11.6469)
Muhamad Efryansyah			(25.11.6470)
Devina Artha Felisha			(25.11.6480)
Kristenthania Merry Jeane Sabubun 	(25.11.6489)
Laila Septiani Hidayat 		(25.11.6560)

Deskripsi:
Proyek ini menganalisis tren popularitas album dan artis pada tangga lagu mingguan Spotify dengan fokus pada metrik performa jangka panjang. Analisis dilakukan terhadap beberapa aspek utama:
Dominasi & Performa: Menghitung total skor popularitas setiap album dan artis menggunakan rumus pembobotan unik ($201 - rank$), yang memberikan apresiasi lebih tinggi bagi konten yang konsisten berada di peringkat atas.
Analisis Produktivitas & Konsistensi: Mengukur jumlah kemunculan (appearances) di tangga lagu, peringkat terbaik (best rank), serta produktivitas artis dalam merilis album unik yang berhasil masuk ke tangga lagu.
Tren Temporal: Menganalisis perubahan performa artis dari bulan ke bulan menggunakan heatmap untuk melihat apakah popularitas sebuah album bersifat musiman atau stabil.
Distribus & Korelasi: Memeriksa korelasi antara durasi tangga lagu (weeks on chart) dengan peringkat yang dicapai, serta melihat distribusi konsistensi peringkat melalui boxplot untuk mengidentifikasi apakah artis cenderung stabil atau fluktuatif di tangga lagu.

Prasyarat:
Sebelum menjalankan program ini, pastikan Anda telah menginstal **Python 3.8** atau versi terbaru. Proyek ini membutuhkan beberapa *library* eksternal untuk pemrosesan data, visualisasi, dan antarmuka terminal:

* **`pandas`**: Digunakan untuk manipulasi dan analisis data (pembersihan, *grouping*, dan agregasi).
* **`matplotlib`**: Digunakan untuk pembuatan seluruh visualisasi grafik (bar, *heatmap*, *boxplot*, dan *pie chart*).
* **`rich`**: Digunakan untuk mempercantik tampilan antarmuka di terminal (menambahkan *progress bar*, *panel*, dan warna pada teks).

Struktur folder:

spotify-project/
|
+---dataset/
|   \---charts_albums_weekly.csv
|
+---output_analisis/
|
+---main1.py
+---utils1.py
\---README.md

Panduan cara menjalankan program melalui terminal:
Sebelum menjalankan program untuk pertama kali, pastikan library pendukung sudah terinstal.
kemudian tinggal mengetikkan "python main.py" karena file kelompok kami diberi nama main1.py maka tinggal mengetikkan phyton main1.py di terminal.
