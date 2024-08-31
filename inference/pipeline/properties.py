from inference.configs.constants import *
import math
import os


def set_tracker_properties(config, elements):
    tracker = elements["nvtracker"]
    for key in config['tracker']:
        if key == 'tracker-width':
            tracker_width = config.getint('tracker', key)
            tracker.set_property('tracker-width', tracker_width)
        if key == 'tracker-height':
            tracker_height = config.getint('tracker', key)
            tracker.set_property('tracker-height', tracker_height)
        if key == 'gpu-id':
            tracker_gpu_id = config.getint('tracker', key)
            tracker.set_property('gpu_id', tracker_gpu_id)
        if key == 'll-lib-file':
            tracker_ll_lib_file = config.get('tracker', key)
            tracker.set_property('ll-lib-file', tracker_ll_lib_file)
        if key == 'll-config-file':
            tracker_ll_config_file = config.get('tracker', key)
            tracker.set_property('ll-config-file', tracker_ll_config_file)
    

    return config, elements


def set_tiler_properties(elements, number_sources):
    tiler = elements["nvtiler"]
    tiler_rows=int(math.sqrt(number_sources))
    tiler_columns=int(math.ceil((1.0*number_sources) / tiler_rows))
    tiler.set_property("rows", tiler_rows)
    tiler.set_property("columns", tiler_columns)
    tiler.set_property("width", TILED_OUTPUT_WIDTH)
    tiler.set_property("height", TILED_OUTPUT_HEIGHT)

    return tiler


def set_streammux_properties(elements):
    streammux = elements["streammux"]
    streammux.set_property('width', 1920)
    streammux.set_property('height', 1080)
    streammux.set_property('batch-size', 1)
    streammux.set_property('batched-push-timeout', MUXER_BATCH_TIMEOUT_USEC)
    streammux.set_property('nvbuf-memory-type', 2)

    return streammux
    
    
def set_pgie_properties(elements, number_sources):
    pgie = elements["pgie"]
    pgie.set_property('config-file-path', PGIE_CONFIG_FILE)
    pgie.set_property("batch-size", number_sources)

    return pgie

def set_osd_properties(elements):
    nvosd = elements["nvosd"]
    nvosd.set_property('process-mode', OSD_PROCESS_MODE)
    nvosd.set_property('display-text', OSD_DISPLAY_TEXT)

    return nvosd
