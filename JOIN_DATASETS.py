import os

FILES_TO_JOIN = [
    "RSMC_hycom_20260904.nc",
    "rsmc_combined_ww3_20260903.nc"
]

def join_file(target_filename):
    if os.path.exists(target_filename):
        print(f"Target file already exists: {target_filename}. Skipping join.")
        return

    print(f"\n--- Joining parts into {target_filename} ---")
    part_num = 1
    parts = []
    
    while True:
        part_name = f"{target_filename}.part{part_num}"
        if os.path.exists(part_name):
            parts.append(part_name)
            part_num += 1
        else:
            break
            
    if not parts:
        print(f"No parts found for {target_filename}.")
        return

    print(f"Found {len(parts)} parts. Recombining...")
    with open(target_filename, 'wb') as f_out:
        for p in parts:
            print(f"  Appending {p}...")
            with open(p, 'rb') as f_in:
                while True:
                    chunk = f_in.read(64 * 1024 * 1024)
                    if not chunk:
                        break
                    f_out.write(chunk)
                    
    print(f"Reconstructed {target_filename} ({os.path.getsize(target_filename) / (1024**3):.2f} GB)")

if __name__ == "__main__":
    for f in FILES_TO_JOIN:
        join_file(f)
