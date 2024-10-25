from configs.constants import *
import math
import gi # type: ignore
gi.require_version('Gst', '1.0')
from gi.repository import Gst # type: ignore
import pyds # type: ignore

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
    streammux.set_property('width', 1280)
    streammux.set_property('height', 720)
    streammux.set_property('batch-size', 1)
    streammux.set_property('batched-push-timeout', MUXER_BATCH_TIMEOUT_USEC)
    # streammux.set_property('nvbuf-memory-type', 2)

    return streammux
    
    
def set_pgie_properties(elements, number_sources):
    pgie = elements["pgie"]
    pgie.set_property('config-file-path', PGIE_CONFIG_FILE)
    pgie.set_property("batch-size", number_sources)
    return pgie

def set_output_properties(elements, stream_output, number_sources, filename):
    if stream_output == "none":
        elements["sink"].set_property('enable-last-sample', 0)
        elements["sink"].set_property('sync', 0)
    
    if stream_output in ("file", "rtsp", "display"):
        # elements["filter_tiler"].set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), format=RGBA"))
        tiler_rows=int(math.sqrt(number_sources))
        tiler_columns=int(math.ceil((1.0*number_sources)/tiler_rows))
        elements["nvtiler"].set_property("rows",tiler_rows)
        elements["nvtiler"].set_property("columns",tiler_columns)
        elements["nvtiler"].set_property("width", TILED_OUTPUT_WIDTH)
        elements["nvtiler"].set_property("height", TILED_OUTPUT_HEIGHT)

        elements["nvosd"].set_property('process-mode',OSD_PROCESS_MODE)
        elements["nvosd"].set_property('display-text',OSD_DISPLAY_TEXT)

        if stream_output in ("file", "rtsp"):
            elements["filter_encoder"].set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), format=I420"))
            elements["encoder"].set_property('bitrate', 4097152)

            if stream_output == "file":
                elements["sink"].set_property('location', f'{filename}_processed.mp4')
                elements["sink"].set_property('sync', 0)
            
            if stream_output == "rtsp":
                elements["sink"].set_property('host', "127.0.0.1")
                elements["sink"].set_property('port', 8245)
                elements["sink"].set_property('async', False)
                elements["sink"].set_property('sync', 1)

    return elements



 