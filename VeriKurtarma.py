import os
import logging
import re
from tkinter import *
from tkinter import messagebox
import threading
from PIL import Image, ImageTk
from logging.handlers import RotatingFileHandler
from tkinter import Tk, StringVar, Text, N, W, E, S
from tkinter import ttk, PhotoImage
from tkinter.font import Font
from ttkthemes import ThemedTk

# Loglama ayarları
log_handler = RotatingFileHandler('recovery.log', maxBytes=10**6, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(formatter)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(log_handler)

# Okuma boyutu
size = 4096  

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
        logger.error(f"Geçersiz sürücü harfi: {drive_letter}")
        raise ValueError("Geçersiz sürücü harfi. Tek bir alfabe karakteri olmalıdır.")
    drive = f"\\\\.\\{drive_letter.upper()}:"
    if not os.path.exists(drive):
        logger.error(f"Disk {drive} mevcut değil veya erişilebilir değil")
        raise FileNotFoundError(f"Disk {drive} mevcut değil veya erişilebilir değil")
    return drive

# Sürücüyü açma
def open_drive(drive):
    try:
        return open(drive, "rb")
    except Exception as e:
        logger.exception(f"Disk açılamadı {drive}")
        raise

# Add a global pause flag
pause_thread = threading.Event()

# Add a global stop flag
stop_thread = False

preview_label = None
# Dosyaları kurtarma

def recover_files(fileD, log_text, recovered_files_label):
    global stop_thread, preview_label
    offs = 0
    drec = False
    kurtarID = 1
    byte = fileD.read(size)
    rar_found = False  # Flag to indicate if a RAR file has been found
    zip_found = False  # Flag to indicate if a ZIP file has been found

    while byte:
        try:
            if stop_thread:
                state.set("Durduruldu")  # Update the state
                logger.info("Recovery process stopped by user.")
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
                        logger.info(f'{filetype.upper()} found at offset: {str(hex(match.start()+(size*offs)))}')
                        log_text.delete(1.0, END)
                        log_text.insert(END, read_logs())
                        try:
                            filename = str(kurtarID) + extension
                            fileN = open(filename, "wb")
                        except Exception as e:
                            logger.exception(f"Output file could not be opened: {e}")
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
                                logger.info(f'{filetype.upper()} written: {filename}')
                                drec = False
                                kurtarID += 1
                                fileN.close()
                                log_text.delete(1.0, END)
                                log_text.insert(END, read_logs())
                                recovered_files_label.config(text=f"Geri getirilen dosya: {kurtarID}")

                                # Show a preview of the recovered file
                                if os.path.exists(filename):
                                    if extension in ['.jpg', '.png', '.bmp', '.gif']:
                                        try:
                                            # For images, use PIL to open the image and create a thumbnail
                                            img = Image.open(filename)
                                            img.thumbnail((100, 100))  # Create a thumbnail with a size of 100x100
                                            tk_img = ImageTk.PhotoImage(img)
                                            preview_label.config(image=tk_img)
                                            preview_label.image = tk_img  # Keep a reference to the image to prevent it from being garbage collected
                                        except OSError:
                                            logger.exception(f"Thumbnail could not be opened and created for image: {filename}")
                            else: 
                                fileN.write(byte)
        except Exception as e:
            logger.exception(f"An error occurred while recovering files: {e}")
            log_text.delete(1.0, END)
            log_text.insert(END, read_logs())
        finally:
            byte = fileD.read(size)
            offs += 1
    fileD.close()
    logger.info("Recovery process completed.")

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
        state.set("Çalışıyor")  # Update the state
        drive_letter = drive_letter_entry.get()
        try:
            drive = validate_drive(drive_letter)
            fileD = open_drive(drive)
            global recovery_thread
            recovery_thread = threading.Thread(target=recover_files, args=(fileD, log_text, recovered_files_label))
            recovery_thread.daemon = True  # Make the thread a daemon thread
            recovery_thread.start()
            progress.start()  # Start the progress bar
            logger.info("Recovery process started.")
        except Exception as e:
            logger.exception("An error occurred while starting the recovery.")
            messagebox.showerror("Hata", str(e))

    def stop_recovery():
        global stop_thread
        if recovery_thread.is_alive():
            messagebox.showinfo("Info", "İşlem yakında durdurulacak..")
            stop_thread = True
            state.set("İşlem durduruluyor")  # Update the state
            progress.stop()  # Stop the progress bar
            logger.info("Stopping recovery process.")
            if not recovery_thread.is_alive():
                messagebox.showinfo("Info", "Kurtarma işlemi başarıyla durduruldu.")
                logger.info("Recovery process successfully stopped.")

    def pause_recovery():
        pause_thread.clear()  # Clear the event to block the thread
        state.set("Durduruldu")  # Update the state
        progress.stop()  # Stop the progress bar
        logger.info("Recovery process paused.")

    def resume_recovery():
        global stop_thread
        stop_thread = False  # Reset the stop_thread flag
        pause_thread.set()  # Set the event to unblock the thread
        state.set("Çalışıyor")  # Update the state
        progress.start()  # Start the progress bar
        logger.info("Recovery process resumed.")

    root = ThemedTk(theme="black")  # Use the "black" theme
    root.title("File Recovery")
    root.configure(bg='#424242')     # Define a custom font
    customFont = Font(family="Helvetica", size=12)
    progress = ttk.Progressbar(root, length=100, mode='indeterminate')
    progress.grid(row=6, column=0, columnspan=2, padx=10, pady=10)
    global state
    state = StringVar()

    # Create a frame for the input fields
    input_frame = ttk.Frame(root)
    input_frame.grid(row=0, column=0, padx=10, pady=10, sticky='ew')

    ttk.Label(input_frame, text="Disk Harfi:", font=customFont).grid(row=0, column=0, padx=10, pady=10)
    drive_letter_entry = ttk.Entry(input_frame)
    drive_letter_entry.grid(row=0, column=1, padx=10, pady=10)

    log_text = Text(root, font=('Consolas', 10), bg='#4f4f4f', fg='white')  # Set the background and foreground colors
    log_text.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')
    scrollbar = ttk.Scrollbar(root, command=log_text.yview)
    scrollbar.grid(row=1, column=2, sticky='ns')
    log_text['yscrollcommand'] = scrollbar.set

    recovered_files_label = ttk.Label(root, text="Geri getirilen dosyalar: 0", font=customFont)
    recovered_files_label.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

    # Add a label to display the state
    state_label = ttk.Label(root, textvariable=state, font=customFont)
    state_label.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

    # Add a label to display the preview
    global preview_label
    preview_label = ttk.Label(root, font=customFont)
    preview_label.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

    # Create a frame for the buttons
    button_frame = ttk.Frame(root)
    button_frame.grid(row=5, column=0, padx=10, pady=10, sticky='ew', columnspan=2)

    button_frame.columnconfigure(0, weight=1)
    button_frame.columnconfigure(1, weight=1)
    button_width = 20  # adjust this value as needed

    ttk.Button(button_frame, text="Kurtarmayı Başlat", command=start_recovery, width=button_width).grid(row=0, column=0, padx=10, pady=10)
    ttk.Button(button_frame, text="Kurtarmayı Durdur", command=stop_recovery, width=button_width).grid(row=0, column=1, padx=10, pady=10)
    ttk.Button(button_frame, text="Kurtarmayı Duraklat", command=pause_recovery, width=button_width).grid(row=1, column=0, padx=10, pady=10)
    ttk.Button(button_frame, text="Kurtarmayı Sürdür", command=resume_recovery, width=button_width).grid(row=1, column=1, padx=10, pady=10)
    root.mainloop()

# Ana fonksiyonu çağırma
if __name__ == "__main__":
    main()
