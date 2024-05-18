import os
import logging
import re
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import threading

# Loglama ayarları
logging.basicConfig(filename='recovery.log', level=logging.INFO)

# Okuma boyutu
size = 8192  

# Dosya imzaları
signatures = {
    'jpeg': (b'\xff\xd8\xff\xe0\x00\x10\x4a\x46', b'\xff\xd9', '.jpg'),
    'png': (b'\x89PNG\r\n\x1a\n', b'\x00\x00\x00\x00IEND\xaeB`\x82', '.png'),
    'gif': (b'GIF89a', b'\x00\x3b', '.gif'),
    'pdf': (b'%PDF-', b'%%EOF', '.pdf'),
    'rar': (b'Rar!\x1A\x07\x00', None, '.rar'),  # RAR signature
    'zip': (b'\x50\x4b\x03\x04', b'\x50\x4b\x05\x06', '.zip'),  # ZIP signature
}

# Başlangıç imzaları için regex
start_regex = re.compile(b'|'.join(start for start, _, _ in signatures.values()))

# Sürücü harfini doğrulama
def validate_drive(drive_letter):
    if not drive_letter.isalpha() or len(drive_letter) != 1:
        raise ValueError("Geçersiz sürücü harfi")
    drive = f"\\\\.\\{drive_letter.upper()}:"
    if not os.path.exists(drive):
        raise FileNotFoundError(f"Disk {drive} mevcut değil veya erişilebilir değil")
    return drive

# Sürücüyü açma
def open_drive(drive):
    try:
        return open(drive, "rb")
    except Exception as e:
        logging.error(f"Disk açılamadı {drive}: {e}")
        raise

# Add a global pause flag
pause_thread = threading.Event()

# Add a global stop flag
stop_thread = False



# Dosyaları kurtarma
def recover_files(fileD, log_text, recovered_files_label):
    global stop_thread
    offs = 0
    drec = False
    kurtarID = 0
    byte = fileD.read(size)
    rar_found = False  # Flag to indicate if a RAR file has been found
    zip_found = False  # Flag to indicate if a ZIP file has been found

    while byte:
        if stop_thread:
            state.set("Stopped")  # Update the state
            break
        pause_thread.wait()  # This will block if the event is cleared
        match = start_regex.search(byte)
        if match:
            for filetype, (start, end, extension) in signatures.items():
                if byte[match.start():match.start()+len(start)] == start:
                    if filetype == 'rar':
                        if rar_found:  # If a RAR file has already been found, skip this iteration
                            continue
                        else:
                            rar_found = True  # Set the flag to True
                    elif filetype == 'zip':
                        if zip_found:  # If a ZIP file has already been found, skip this iteration
                            continue
                        else:
                            zip_found = True  # Set the flag to True
                    drec = True
                    logging.info(f'{filetype.upper()} konumda bulundu: {str(hex(match.start()+(size*offs)))}')
                    log_text.delete(1.0, END)
                    log_text.insert(END, read_logs())
                    try:
                        fileN = open(str(kurtarID) + extension, "wb")
                    except Exception as e:
                        logging.error(f"Çıktı dosyası açılamadı: {e}")
                        log_text.delete(1.0, END)
                        log_text.insert(END, read_logs())
                        continue
                    fileN.write(byte[match.start():])
                    while drec:
                        byte = fileD.read(size)
                        bfind = byte.find(end)
                        if bfind >= 0:
                            fileN.write(byte[:bfind+len(end)])
                            fileD.seek((offs+1)*size)
                            logging.info(f'{filetype.upper()} yazildi: {str(kurtarID)}{extension}')
                            drec = False
                            kurtarID += 1
                            fileN.close()
                            log_text.delete(1.0, END)
                            log_text.insert(END, read_logs())
                            recovered_files_label.config(text=f"Recovered Files: {kurtarID}")
                        else: 
                            fileN.write(byte)
        byte = fileD.read(size)
        offs += 1
    fileD.close()
# Log dosyasını okuma
def read_logs():
    with open('recovery.log', 'r') as f:
        return f.read()

# Ana fonksiyon
def main():
    
    def start_recovery():
        
        global stop_thread
        stop_thread = False
        pause_thread.set()  # Set the event to unblock the thread
        state.set("Running")  # Update the state
        drive_letter = drive_letter_entry.get()
        try:
            drive = validate_drive(drive_letter)
            fileD = open_drive(drive)
            global recovery_thread
            recovery_thread = threading.Thread(target=recover_files, args=(fileD, log_text, recovered_files_label))
            recovery_thread.daemon = True  # Make the thread a daemon thread
            recovery_thread.start()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def stop_recovery():
        global stop_thread
        if recovery_thread.is_alive():
            messagebox.showinfo("Info", "Recovery process will be stopped soon.")
            stop_thread = True
            state.set("Stopping")  # Update the state

    def pause_recovery():
        pause_thread.clear()  # Clear the event to block the thread
        state.set("Paused")  # Update the state

    def resume_recovery():
        global stop_thread
        stop_thread = False  # Reset the stop_thread flag
        pause_thread.set()  # Set the event to unblock the thread
        state.set("Running")  # Update the state

    root = Tk()
    root.title("File Recovery")

    global state
    state = StringVar()

    Label(root, text="Drive Letter:").grid(row=0, column=0, padx=10, pady=10)
    drive_letter_entry = Entry(root)
    drive_letter_entry.grid(row=0, column=1, padx=10, pady=10)

    log_text = Text(root)
    log_text.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

    recovered_files_label = Label(root, text="Recovered Files: 0")
    recovered_files_label.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

    # Add a label to display the state
    state_label = Label(root, textvariable=state)
    state_label.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

    Button(root, text="Start Recovery", command=start_recovery).grid(row=4, column=0, padx=10, pady=10)
    Button(root, text="Stop Recovery", command=stop_recovery).grid(row=4, column=1, padx=10, pady=10)
    Button(root, text="Pause Recovery", command=pause_recovery).grid(row=5, column=0, padx=10, pady=10)
    Button(root, text="Resume Recovery", command=resume_recovery).grid(row=5, column=1, padx=10, pady=10)

    root.mainloop()

# Ana fonksiyonu çağırma
if __name__ == "__main__":
    main()