# Department Network Simulation with Ryu Controller

## Scenario
Simulasi jaringan dengan 3 departemen yang memiliki aturan konektivitas tertentu:

### Topologi
- **Department A**: Switch s1 dengan Host h1 (10.0.1.1) dan Host h2 (10.0.1.2)
- **Department B**: Switch s2 dengan Host h3 (10.0.2.1) dan Host h4 (10.0.2.2)
- **Department C**: Switch s3 dengan Host h5 (10.0.3.1) dan Host h6 (10.0.3.2)

### Aturan Koneksi
- **Dept A → Dept B**: ✅ Bisa connect
- **Dept A → Dept C**: ❌ Tidak bisa connect
- **Dept B → Dept C**: ✅ Bisa connect
- **Dept C → Dept A**: ❌ Tidak bisa connect

## File yang Dibuat
1. `departemen_topology.py` - File topologi Mininet
2. `departemen_controller.py` - File Ryu controller
3. `simulasi.py` - File Untuk Simulasi Mininet Otomatis

## Cara Menjalankan

### 1. Install Dependencies
```bash
# Install Mininet (jika belum)
sudo apt-get install mininet

# Install Ryu
pip install ryu
```

### 2. Jalankan Controller
```bash
# Buka terminal baru
ryu-manager departemen_controller.py
```

### 3. Jalankan Topologi
```bash
# Buka terminal lain
sudo python departemen_topology.py
```

### 4. Testing Koneksi
Setelah topologi berjalan, gunakan perintah berikut untuk testing:

```bash
# Testing dalam departemen yang sama (harus berhasil)
mininet> ping h1 h2    # Dept A internal
mininet> ping h3 h4    # Dept B internal
mininet> ping h5 h6    # Dept C internal

# Testing antar departemen
mininet> ping h1 h3    # Dept A → Dept B (harus berhasil)
mininet> ping h1 h5    # Dept A → Dept C (harus gagal)
mininet> ping h3 h5    # Dept B → Dept C (harus berhasil)
mininet> ping h5 h1    # Dept C → Dept A (harus gagal)
```

