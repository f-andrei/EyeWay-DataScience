import sys
import gi # type: ignore
gi.require_version('Gst', '1.0')
from gi.repository import GLib, Gst # type: ignore
from common.bus_call import bus_call
from configs.constants import *
from pipeline.analytics_probe import nvanalytics_src_pad_buffer_probe
from pipeline.pipeline import create_pipeline


frame_count = {}
saved_count = {}
perf_data = None


no_display = False
silent = False
file_loop = False
g_on = True
a = None





# Function to run the pipeline
def run_pipeline(args):
    pipeline, analytics, perf_data = create_pipeline(args)
    if not pipeline:
        sys.stderr.write("Failed to create pipeline\n")
        return


    loop = GLib.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect ("message", bus_call, loop)

    nvanalytics_src_pad=analytics.get_static_pad("src")
    if not nvanalytics_src_pad:
        sys.stderr.write(" Unable to get src pad \n")
    else:
        nvanalytics_src_pad.add_probe(Gst.PadProbeType.BUFFER, nvanalytics_src_pad_buffer_probe, 0, perf_data)
        # perf callback function to print fps every 5 sec
        GLib.timeout_add(5000, perf_data.perf_print_callback)

    print("Starting pipeline \n")
    pipeline.set_state(Gst.State.PLAYING)

    try:
        loop.run()
    except Exception as e:
        raise e
        # pass

    pipeline.set_state(Gst.State.NULL)

if __name__ == '__main__':
    run_pipeline(sys.argv)