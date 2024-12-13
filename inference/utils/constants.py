PGIE_CLASS_ID_VEHICLE = 0
PGIE_CLASS_ID_BICYCLE = 1
PGIE_CLASS_ID_PERSON = 2
PGIE_CLASS_ID_ROADSIGN = 3
MUXER_BATCH_TIMEOUT_USEC = 0
TILED_OUTPUT_WIDTH=1280
TILED_OUTPUT_HEIGHT=720 
OSD_PROCESS_MODE= 0
OSD_DISPLAY_TEXT= 1

MIN_CONFIDENCE = 0.3
MAX_CONFIDENCE = 0.4

PGIE_CONFIG_FILE = "/apps/inference/configs/config_pgie_yolo_det.txt"
ANALYTICS_CONFIG_FILE = "/apps/inference/configs/config_nvdsanalytics.txt"
TRACKER_CONFIG_FILE = "/apps/inference/configs/dsnvanalytics_tracker_config.txt"


HLS_OUTPUT_PATH = "/apps/inference/stream"

CLASS_NAMES = ["Pessoa", "Bicicleta", "Carro", "Motocicleta", "Avião", "Ônibus", "Trem", "Caminhão"]

BACKEND_API_URL = "http://172.26.144.1:3000"



