import zipfile
from pysubs2 import SSAFile


def guess_encoding(file_bytes):
    try:
        test = file_bytes.decode('cp1250')
        if any(char in test for char in "ąćęłńóśźż"):  # Sprawdzenie polskich znaków
            return 'cp1250'
    except UnicodeDecodeError:
        pass

    try:
        test = file_bytes.decode('utf-8')
        return 'utf-8'
    except UnicodeDecodeError:
        pass

    return 'cp1251'


def convert_to_srt(content, fps=None):
    subs = SSAFile.from_string(content, fps=fps)
    return subs.to_string("srt")


def extract_and_convert(zip_content, fps):
    with zipfile.ZipFile(zip_content) as zip_file:
        txt_files = [f for f in zip_file.namelist() if f.endswith('.txt') or f.endswith('.srt') or f.endswith('.sub')]
        if not txt_files:
            raise Exception("Brak plików txt w archiwum ZIP")

        txt_file_name = txt_files[0]
        with zip_file.open(txt_file_name) as txt_file:
            raw_data = txt_file.read()
            encoding = guess_encoding(raw_data)
            content = raw_data.decode(encoding)

        return convert_to_srt(content, fps)