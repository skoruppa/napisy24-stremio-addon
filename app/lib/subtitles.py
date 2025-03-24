import zipfile
from pysubs2 import SSAFile
import re


def extract_and_convert(zip_content, fps):
    with zipfile.ZipFile(zip_content) as zip_file:
        for file_name in zip_file.namelist():
            if file_name.endswith(('.txt', '.srt', '.sub')):
                with zip_file.open(file_name) as file:
                    raw_data = file.read()
                    try:
                        encoded = raw_data.decode('cp1250')
                    except UnicodeDecodeError:
                        encoded = raw_data.decode('utf-8')
                    if not fps:
                        match = re.search(r"(\d+\.\d+)\s*fps", encoded)

                        fps = float(match.group(1)) if match else None
                    return SSAFile.from_string(encoded, fps=fps).to_string("srt")
    raise Exception("Brak plików z napisami w archiwum ZIP")
