import argparse
import sys
import gi # type: ignore
gi.require_version('Gst', '1.0')
from gi.repository import GLib, Gst # type: ignore
from common.bus_call import bus_call
from configs.constants import *
from pipeline.analytics_probe import nvanalytics_src_pad_buffer_probe
from pipeline.pipeline import create_pipeline, create_rtsp_server

def parse_args():

    parser = argparse.ArgumentParser(prog="run_pipeline.py",
                    description="EyeWay Inference Pipeline")
    parser.add_argument(
        "-i",
        "--input",
        help="Path to input streams",
        nargs="+",
        metavar="URIs",
        default=["a"],
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output",
        default="display",
        help="Output",
        choices=["display", "file", "rtsp", "none"],
    )

    # Check input arguments
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()
    print(vars(args))
    return args

# Function to run the pipeline
def run_pipeline(args):
    args = parse_args()

    create_rtsp_server()
    pipeline, analytics, perf_data, element_probe = create_pipeline(args)
    if not pipeline:
        sys.stderr.write("Failed to create pipeline\n")
        return

    loop = GLib.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect ("message", bus_call, loop)

    element_probe=element_probe.get_static_pad("src")
    if not element_probe:
        sys.stderr.write(" Unable to get src pad \n")
    else:
        element_probe.add_probe(Gst.PadProbeType.BUFFER, nvanalytics_src_pad_buffer_probe, 0, perf_data)
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