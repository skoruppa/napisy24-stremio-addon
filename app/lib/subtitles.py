import zipfile
from pysubs2 import SSAFile


def extract_and_convert(zip_content, fps):
    with zipfile.ZipFile(zip_content) as zip_file:
        for file_name in zip_file.namelist():
            if file_name.endswith(('.txt', '.srt', '.sub')):
                with zip_file.open(file_name) as file:
                    raw_data = file.read()
                    encoding = 'utf-8' if b'\xef\xbb\xbf' in raw_data[:3] else 'cp1250'
                    return SSAFile.from_string(raw_data.decode(encoding), fps=fps).to_string("srt")
    raise Exception("Brak plików z napisami w archiwum ZIP")
