import requests
import json
import time
import re
from pydub import AudioSegment
from pydub.utils import which
import os
import urllib.request
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from config import main_token
# تنظیم FFmpeg
AudioSegment.converter = which("ffmpeg") or os.path.join(os.path.dirname(sys.executable), "ffmpeg.exe")
AudioSegment.ffprobe = which("ffprobe") or os.path.join(os.path.dirname(sys.executable), "ffprobe.exe")

# توکن API ویرا
main_token = main_token
def parse_srt(file_path):
    """پارس کردن فایل SRT و استخراج متن و زمان‌بندی‌ها"""
    print(f"پارس کردن فایل: {file_path}")
    subtitles = []
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            content = file.read().strip()
            if not content:
                print("فایل SRT خالی است")
                return subtitles
            blocks = content.split('\n\n')
            print(f"تعداد بلوک‌های SRT: {len(blocks)}")
            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) < 2 and not re.match(r'\d{2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,.]\d{3}', lines[0] if lines else ''):
                    print(f"بلوک نامعتبر: {block}")
                    continue

                time_match = None
                text = ""
                start_time = end_time = None
                index = None

                if lines[0].strip().isdigit():
                    index = lines[0].strip()
                    time_match = re.match(r'(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})', lines[1].strip())
                    if time_match:
                        start_time = time_match.group(1)
                        end_time = time_match.group(2)
                        text = ' '.join(line.strip() for line in lines[2:]).strip()
                else:
                    time_match = re.match(r'(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})(?:\s*(.*))?', lines[0].strip())
                    if time_match:
                        start_time = time_match.group(1)
                        end_time = time_match.group(2)
                        text = time_match.group(3) or ''
                        if len(lines) > 1:
                            text += ' ' + ' '.join(line.strip() for line in lines[1:]).strip()
                        index = str(len(subtitles) + 1)

                if time_match:
                    subtitles.append({
                        'index': index,
                        'start_time': start_time,
                        'end_time': end_time,
                        'text': text
                    })
                    print(f"زیرنویس اضافه شد: {text or 'خالی'} (شاخص: {index})")
                else:
                    print(f"خطای فرمت زمان‌بندی در بلوک: {lines[0]}")

            print(f"تعداد زیرنویس‌های استخراج‌شده: {len(subtitles)}")
            return subtitles
    except Exception as e:
        print(f"خطا در پارس فایل SRT: {str(e)}")
        raise

def time_to_milliseconds(time_str):
    """تبدیل زمان SRT به میلی‌ثانیه"""
    try:
        time_str = time_str.strip()
        match = re.match(r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3})', time_str)
        if not match:
            raise ValueError(f"فرمت زمان‌بندی نامعتبر: {time_str}")
        hours, minutes, seconds, milliseconds = match.groups()
        return int(hours) * 3600000 + int(minutes) * 60000 + int(seconds) * 1000 + int(milliseconds)
    except Exception as e:
        print(f"خطا در تبدیل زمان: {str(e)}")
        raise

def send_text(text, speaker, speed, retries=60, retry_delay=10):
    """ارسال متن به API و دریافت توکن با بازآزمایی"""
    print(f"ارسال متن به API: {text} با گوینده {speaker} و سرعت {speed}")
    for attempt in range(retries):
        try:
            url = "https://partai.gw.isahab.ir/TextToSpeech/v1/longText"
            payload = json.dumps({
                "data": text,
                "speed": speed,
                "speaker": speaker
            })
            headers = {
                'Content-Type': 'application/json',
                'gateway-token': main_token
            }
            response = requests.post(url, headers=headers, data=payload, timeout=30)
            response.raise_for_status()
            response_data = response.json()
            token = response_data["data"]["data"]["token"]
            print(f"توکن دریافت شد: {token}")
            return token
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.HTTPError) as e:
            print(f"خطا در تلاش {attempt + 1}/{retries} برای ارسال متن به API: {str(e)}")
            if attempt < retries - 1:
                print(f"صبر برای {retry_delay} ثانیه قبل از تلاش مجدد...")
                time.sleep(retry_delay)
            else:
                print(f"خطا پس از {retries} تلاش: {str(e)}")
                raise Exception(f"نمی‌توان به سرور API متصل شد: {str(e)}")
        except Exception as e:
            print(f"خطا در ارسال متن به API: {str(e)}")
            raise

def check(token, retries=60, retry_delay=10):
    """چک کردن وضعیت توکن و دریافت لینک فایل صوتی با بازآزمایی"""
    print(f"چک کردن وضعیت توکن: {token}")
    for attempt in range(retries):
        try:
            url = f"https://partai.gw.isahab.ir/TextToSpeech/v1/trackingFile/{token}"
            headers = {
                'Content-Type': 'application/json',
                'gateway-token': main_token
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            response_data = response.json()
            file_path = response_data["data"]["filePath"]
            print(f"لینک فایل صوتی: {file_path}")
            return file_path
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.HTTPError) as e:
            print(f"خطا در تلاش {attempt + 1}/{retries} برای چک کردن توکن: {str(e)}")
            if attempt < retries - 1:
                print(f"صبر برای {retry_delay} ثانیه قبل از تلاش مجدد...")
                time.sleep(retry_delay)
            else:
                print(f"خطا پس از {retries} تلاش: {str(e)}")
                raise Exception(f"نمی‌توان به سرور API متصل شد: {str(e)}")
        except Exception as e:
            print(f"خطا در چک کردن توکن: {str(e)}")
            raise

def download_audio(file_path, output_path, retries=60, retry_delay=10):
    """دانلود فایل صوتی از لینک با بازآزمایی"""
    print(f"دانلود فایل صوتی: {file_path} به {output_path}")
    for attempt in range(retries):
        try:
            audio_url = f"https://partai.gw.isahab.ir/TextToSpeech/v1{file_path}"
            urllib.request.urlretrieve(audio_url, output_path)
            print(f"فایل صوتی دانلود شد: {output_path}")
            return
        except urllib.error.HTTPError as e:
            print(f"خطا در تلاش {attempt + 1}/{retries} برای دانلود فایل صوتی: {str(e)}")
            if attempt < retries - 1:
                print(f"صبر برای {retry_delay} ثانیه قبل از تلاش مجدد...")
                time.sleep(retry_delay)
            else:
                print(f"خطا پس از {retries} تلاش: {str(e)}")
                raise Exception(f"خطا در دانلود فایل صوتی: {str(e)}")
        except Exception as e:
            print(f"خطا در دانلود فایل صوتی: {str(e)}")
            raise

def combine_audio(subtitles, output_file="output.wav", speaker="3"):
    """ترکیب فایل‌های صوتی با زمان‌بندی مناسب و ذخیره فایل‌های جداگانه"""
    print(f"شروع ترکیب فایل‌های صوتی برای {len(subtitles)} زیرنویس با گوینده {speaker}")
    if not subtitles:
        raise ValueError("هیچ زیرنویسی برای پردازش وجود ندارد")

    # ثابت‌ها برای محاسبه سرعت
    R_base = 10  # کاراکتر بر ثانیه در سرعت 1.0
    S_min = 0.8  # حداقل سرعت
    S_max = 1.8  # حداکثر سرعت

    output_dir = os.path.splitext(output_file)[0] + "_individual_audios"
    os.makedirs(output_dir, exist_ok=True)
    print(f"پوشه فایل‌های جداگانه ایجاد شد: {output_dir}")

    combined = AudioSegment.silent(duration=0)
    individual_files = []

    for i, subtitle in enumerate(subtitles):
        print(f"پردازش زیرنویس {subtitle['index']}: {subtitle['text'] or 'خالی'}")
        try:
            # محاسبه مدت زمان زیرنویس
            start_ms = time_to_milliseconds(subtitle['start_time'])
            end_ms = time_to_milliseconds(subtitle['end_time'])
            duration_ms = end_ms - start_ms
            if duration_ms <= 0:
                raise ValueError(f"مدت زمان زیرنویس {subtitle['index']} نامعتبر است")

            if not subtitle['text']:  # زیرنویس خالی
                audio = AudioSegment.silent(duration=duration_ms)
                print(f"سکوت برای زیرنویس خالی {subtitle['index']} اضافه شد: {duration_ms} میلی‌ثانیه")
            else:  # زیرنویس با متن
                # محاسبه سرعت
                N = len(subtitle['text'])
                T = duration_ms / 1000  # به ثانیه
                S_required = N / (R_base * T)
                S = max(S_min, min(S_max, S_required))
                print(f"برای زیرنویس {subtitle['index']}: N={N}, T={T:.2f} s, S_required={S_required:.2f}, S={S:.2f}")

                token = send_text(subtitle['text'], speaker, S)
                time.sleep(5)  # انتظار 5 ثانیه
                file_path = check(token)
                audio_file = os.path.join(output_dir, f"subtitle_{subtitle['index']}.mp3")

                download_audio(file_path, audio_file)
                individual_files.append(audio_file)

                audio = AudioSegment.from_file(audio_file)
                if len(audio) < duration_ms:
                    audio += AudioSegment.silent(duration=duration_ms - len(audio))
                print(f"فایل صوتی جداگانه ذخیره شد: {audio_file}")

            if start_ms > len(combined):
                combined += AudioSegment.silent(duration=start_ms - len(combined))
            combined += audio

        except Exception as e:
            error_msg = f"خطا در پردازش زیرنویس {subtitle['index']} (متن: {subtitle['text'] or 'خالی'}): {str(e)}"
            print(error_msg)
            # ذخیره فایل صوتی تا این لحظه
            try:
                if len(combined) > 0:
                    combined.export(output_file, format="wav")
                    print(f"فایل صوتی نهایی تا زیرنویس {subtitle['index']} ذخیره شد: {output_file}")
                    error_msg += f"\nفایل صوتی تا این لحظه در {output_file} ذخیره شد."
                else:
                    print("هیچ صوتی برای ذخیره وجود ندارد")
                    error_msg += "\nهیچ صوتی تولید نشد، فایل خروجی ذخیره نشد."
            except Exception as save_error:
                error_msg += f"\nخطا در ذخیره فایل صوتی: {str(save_error)}"
            raise Exception(error_msg)

    # ذخیره فایل صوتی نهایی اگه همه زیرنویس‌ها موفق باشن
    try:
        combined.export(output_file, format="wav")
        print(f"فایل صوتی نهایی ذخیره شد: {output_file}")
    except Exception as e:
        print(f"خطا در ذخیره فایل صوتی نهایی {output_file}: {str(e)}")
        raise Exception(f"خطا در ذخیره فایل صوتی نهایی: {str(e)}")

    return output_dir

def merge_audio_files(audio_files, output_file="output2.wav"):
    """ترکیب چندین فایل صوتی به یک فایل"""
    print(f"شروع ترکیب {len(audio_files)} فایل صوتی")
    if not audio_files:
        raise ValueError("هیچ فایل صوتی برای ترکیب انتخاب نشده است")

    combined = AudioSegment.silent(duration=0)
    for audio_file in audio_files:
        print(f"اضافه کردن فایل: {audio_file}")
        try:
            if not os.path.exists(audio_file):
                raise FileNotFoundError(f"فایل {audio_file} یافت نشد")
            if not audio_file.lower().endswith(('.mp3', '.wav')):
                raise ValueError(f"فرمت فایل {audio_file} پشتیبانی نمی‌شود")
            audio = AudioSegment.from_file(audio_file)
            combined += audio
        except Exception as e:
            print(f"خطا در پردازش فایل {audio_file}: {str(e)}")
            raise Exception(f"خطا در پردازش فایل {audio_file}: {str(e)}")

    try:
        combined.export(output_file, format="wav")
        print(f"فایل صوتی ترکیب‌شده ذخیره شد: {output_file}")
    except Exception as e:
        print(f"خطا در ذخیره فایل خروجی {output_file}: {str(e)}")
        raise Exception(f"خطا در ذخیره فایل خروجی: {str(e)}")

def create_gui():
    """ایجاد رابط کاربری گرافیکی"""
    root = tk.Tk()
    root.title("تبدیل زیرنویس به صوت")
    root.geometry("400x450")

    srt_file = tk.StringVar()
    output_file = tk.StringVar(value="output.wav")
    estimated_label = tk.Label(root, text="زمان تقریبی پردازش: -")
    output_dir_label = tk.Label(root, text="پوشه فایل‌های جداگانه: -")
    merge_output_label = tk.Label(root, text="فایل صوتی ترکیب‌شده: -")
    speaker_var = tk.StringVar(value="3")  # گوینده پیش‌فرض

    def select_srt_file():
        file_path = filedialog.askopenfilename(filetypes=[("SRT files", "*.srt")])
        if file_path:
            srt_file.set(file_path)
            try:
                subtitles = parse_srt(file_path)
                estimated_time = len(subtitles) * 5
                estimated_label.config(text=f"زمان تقریبی پردازش: {estimated_time} ثانیه")
                output_dir_label.config(text="پوشه فایل‌های جداگانه: -")
                merge_output_label.config(text="فایل صوتی ترکیب‌شده: -")
            except Exception as e:
                messagebox.showerror("خطا", f"خطا در پارس فایل SRT: {str(e)}")
                estimated_label.config(text="زمان تقریبی پردازش: -")
                output_dir_label.config(text="پوشه فایل‌های جداگانه: -")
                merge_output_label.config(text="فایل صوتی ترکیب‌شده: -")

    def select_output_file():
        file_path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV files", "*.wav")])
        if file_path:
            output_file.set(file_path)
            output_dir_label.config(text="پوشه فایل‌های جداگانه: -")
            merge_output_label.config(text="فایل صوتی ترکیب‌شده: -")

    def run_conversion():
        if not srt_file.get():
            messagebox.showerror("خطا", "لطفاً یک فایل SRT انتخاب کنید.")
            return
        try:
            subtitles = parse_srt(srt_file.get())
            if not subtitles:
                messagebox.showerror("خطا", "فایل SRT خالی است یا فرمت آن معتبر نیست.")
                return
            combine_button.config(state="disabled")
            merge_button.config(state="disabled")
            estimated_label.config(text="در حال پردازش...")
            output_dir_label.config(text="پوشه فایل‌های جداگانه: -")
            merge_output_label.config(text="فایل صوتی ترکیب‌شده: -")
            root.update()
            output_dir = combine_audio(subtitles, output_file.get(), speaker_var.get())
            messagebox.showinfo("موفقیت",
                                f"فایل صوتی کامل در {output_file.get()} ذخیره شد.\nفایل‌های جداگانه در {output_dir} ذخیره شدند.")
            estimated_label.config(text=f"زمان تقریبی پردازش: {len(subtitles) * 5} ثانیه")
            output_dir_label.config(text=f"پوشه فایل‌های جداگانه: {output_dir}")
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در پردازش: {str(e)}")
        finally:
            combine_button.config(state="normal")
            merge_button.config(state="normal")

    def merge_selected_audio_files():
        audio_files = filedialog.askopenfilenames(filetypes=[("Audio files", "*.mp3 *.wav")])
        if not audio_files:
            messagebox.showerror("خطا", "هیچ فایل صوتی انتخاب نشده است.")
            return
        try:
            merge_button.config(state="disabled")
            combine_button.config(state="disabled")
            estimated_label.config(text="در حال ترکیب فایل‌های صوتی...")
            merge_output_label.config(text="فایل صوتی ترکیب‌شده: -")
            root.update()
            output_dir = os.path.dirname(audio_files[0]) if audio_files else "."
            output_path = os.path.join(output_dir, "output2.wav")
            merge_audio_files(audio_files, output_path)
            messagebox.showinfo("موفقیت", f"فایل صوتی ترکیب‌شده در\n{output_path}\nذخیره شد.")
            estimated_label.config(text="زمان تقریبی پردازش: -")
            merge_output_label.config(text=f"فایل صوتی ترکیب‌شده: {output_path}")
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در ترکیب فایل‌های صوتی: {str(e)}")
        finally:
            merge_button.config(state="normal")
            combine_button.config(state="normal")

    tk.Label(root, text="فایل SRT:").pack(pady=10)
    tk.Entry(root, textvariable=srt_file, width=40).pack()
    tk.Button(root, text="انتخاب فایل SRT", command=select_srt_file).pack(pady=5)

    tk.Label(root, text="فایل خروجی (WAV):").pack(pady=10)
    tk.Entry(root, textvariable=output_file, width=40).pack()
    tk.Button(root, text="انتخاب مسیر خروجی", command=select_output_file).pack(pady=5)

    tk.Label(root, text="انتخاب گوینده:").pack(pady=5)
    speaker_combobox = ttk.Combobox(root, textvariable=speaker_var, values=["1", "2", "3"], state="readonly")
    speaker_combobox.pack(pady=5)

    estimated_label.pack(pady=10)
    output_dir_label.pack(pady=10)
    merge_output_label.pack(pady=10)

    combine_button = tk.Button(root, text="شروع تبدیل", command=run_conversion)
    combine_button.pack(pady=10)

    merge_button = tk.Button(root, text="ترکیب فایل‌های صوتی", command=merge_selected_audio_files)
    merge_button.pack(pady=10)

    root.mainloop()

def main(srt_file, output_file="output.wav", speaker="3"):
    """تابع اصلی برای تبدیل فایل SRT به صوت"""
    subtitles = parse_srt(srt_file)
    output_dir = combine_audio(subtitles, output_file, speaker)
    print(f"فایل صوتی کامل در {output_file} ذخیره شد.\nفایل‌های جداگانه در {output_dir} ذخیره شدند.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        srt_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "output.wav"
        speaker = sys.argv[3] if len(sys.argv) > 3 else "3"
        main(srt_file, output_file, speaker)
    else:
        create_gui()