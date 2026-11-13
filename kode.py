import json
import sys


def muat_kb(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def lengkapi_aturan(kb):
    """Isi kolom 'jenis' dan 'detail' bila JSON tidak memilikinya."""
    for a in kb["aturan"]:
        m = a["maka"].lower()
        if "jenis" not in a:
            if m.startswith("formasi"):
                a["jenis"] = "formasi"
            elif m.startswith(("gaya menyerang", "menyerang")):
                a["jenis"] = "menyerang"
            elif m.startswith(("gaya bertahan", "bertahan")):
                a["jenis"] = "bertahan"
            elif m.startswith("saran"):
                a["jenis"] = "saran"
            else:
                a["jenis"] = "analisis"
        a.setdefault("detail", a["maka"])


def terpenuhi(aturan, memori):
    ada = [s in memori for s in aturan["jika"]]
    return all(ada) if aturan["mode"] == "dan" else any(ada)


def tanya_yt(teks):
    while True:
        j = input(f"{teks} (y/t) > ").strip().lower()
        if j in ("y", "t"):
            return j == "y"
        print("  Jawab y atau t.")


def kumpulkan_fakta(kb):
    """Tanya user hanya fakta yang tidak pernah menjadi hasil aturan."""
    memori = []
    hasil_aturan = {a["maka"] for a in kb["aturan"]}

    # Formasi lawan: pilih satu saja (saling eksklusif).
    # Daftar pilihan diambil otomatis dari syarat "lawan formasi ..." di aturan.
    pilihan = []
    for a in kb["aturan"]:
        for s in a["jika"]:
            if s.startswith("lawan formasi") and s not in hasil_aturan and s not in pilihan:
                pilihan.append(s)
    ps = {"judul": "Formasi lawan", "pilihan": pilihan}
    print(f"Pilih {ps['judul'].lower()}:")
    for i, p in enumerate(ps["pilihan"], 1):
        print(f"  {i}. {p.replace('lawan formasi ', '')}")
    while True:
        j = input("Nomor pilihan > ").strip()
        if j.isdigit() and 1 <= int(j) <= len(ps["pilihan"]):
            memori.append(ps["pilihan"][int(j) - 1])
            break
        print("  Nomor tidak valid.")
    print("\nJawab y/t.")

    sudah = set(ps["pilihan"])
    no = 1
    for a in kb["aturan"]:
        for s in a["jika"]:
            if s in sudah or s in hasil_aturan:
                continue
            sudah.add(s)
            teks = f"Apakah {s}?"  # pertanyaan dibuat otomatis dari teks fakta
            if tanya_yt(f"{no}. {teks}"):
                memori.append(s)
            no += 1
    return memori


def forward_chaining(kb, memori):
    """Mengembalikan (memori akhir, asal: fakta -> aturan, daftar siklus)."""
    memori = list(memori)
    asal = {}
    siklus = []
    while True:
        cocok = [a for a in kb["aturan"]
                 if a["maka"] not in memori and terpenuhi(a, memori)]
        if not cocok:
            break
        r = cocok[0]  # ambil aturan pertama
        memori.append(r["maka"])
        asal[r["maka"]] = r
        siklus.append(r)
    return memori, asal, siklus


def cetak_alasan(fakta, asal, memori, indent=2, dicetak=None):
    r = asal[fakta]
    syarat = [s for s in r["jika"] if s in memori]
    print(f"{' ' * indent}{fakta} <- {r['id']} ({', '.join(syarat)})")
    for s in syarat:
        if s in asal:
            cetak_alasan(s, asal, memori, indent + 2)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "based-rule.json"
    kb = muat_kb(path)
    lengkapi_aturan(kb)

    print(kb["judul"])
    awal = kumpulkan_fakta(kb)
    print("\nFakta awal:", ", ".join(awal) if awal else "(tidak ada)")

    memori, asal, siklus = forward_chaining(kb, awal)

    print()
    for i, r in enumerate(siklus, 1):
        print(f"Siklus {i}: {r['id']} -> {r['maka']}")
    print(f"Siklus {len(siklus) + 1}: tidak ada aturan baru, berhenti")

    print("\nKesimpulan:")
    ringkas = [("formasi", "Formasi"), ("menyerang", "Gaya menyerang"),
               ("bertahan", "Gaya bertahan")]
    for jenis, label in ringkas:
        hasil = [r["maka"].split(": ", 1)[-1].replace("formasi ", "", 1)
                 if jenis == "formasi" else r["maka"].split(": ", 1)[-1]
                 for r in siklus if r["jenis"] == jenis]
        print(f"  {label:<15}: {'; '.join(hasil) if hasil else 'tidak ada aturan yang cocok'}")
    ada = True
    if not ada:
        print("  Tidak ada rekomendasi yang cocok dengan jawaban Anda.")
    else:
        print("\nAlasan:")
        for r in siklus:
            cetak_alasan(r["maka"], asal, memori)

    print("\nCatatan:", kb["batas"])


if __name__ == "__main__":
    main()