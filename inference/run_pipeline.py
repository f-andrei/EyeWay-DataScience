import argparse
import csv
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
    return args

# Function to run the pipeline
def run_pipeline(args):
    args = parse_args()
    if args.output == "rtsp":
        create_rtsp_server()

    period = args.input[0].split(".")[0].split("/")[-1].split("_")

    pipeline, analytics, perf_data, element_probe = create_pipeline(args)
    if not pipeline:
        sys.stderr.write("Failed to create pipeline\n")
        return

    loop = GLib.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, loop)

    element_probe = element_probe.get_static_pad("src")
    if not element_probe:
        sys.stderr.write("Unable to get src pad\n")
    else:
        vehicle_counter = {
            "G1": {"Carro": set(), "Moto": set(), "Onibus": set(), "Caminhao": set()},
            "G2": {"Carro": set(), "Moto": set(), "Onibus": set(), "Caminhao": set()},
            "G3": {"Carro": set(), "Moto": set(), "Onibus": set(), "Caminhao": set()},
        }
        element_probe.add_probe(Gst.PadProbeType.BUFFER, nvanalytics_src_pad_buffer_probe, 0, perf_data, vehicle_counter)
        GLib.timeout_add(5000, perf_data.perf_print_callback)

    print("Starting pipeline\n")

    try:
        # Attempt to start the pipeline
        pipeline.set_state(Gst.State.PLAYING)
        loop.run()

    except KeyboardInterrupt:
        print("Keyboard Interrupt detected, exiting...")

    except Exception as e:
        print(f"Error occurred: {e}")

    finally:
        # Ensure that resources are properly cleaned up
        print("Exiting app\n")
        write_vehicle_counter_to_csv(vehicle_counter, period)
        pipeline.set_state(Gst.State.NULL)

def write_vehicle_counter_to_csv(vehicle_counter, period="6:30-7:00"):
    try:
        print("Attempting to write vehicle counter to CSV")
        period = "-".join(period)
        start, end = period.split('-')
        start = f"{start[:2]}:{start[2:]}"
        end = f"{end[:2]}:{end[2:]}"
        period = f"{start}-{end}"
    except ValueError as e:
        print(f"Invalid period format: {e}")
        return
    except Exception as e:
        print(f"An error occurred: {e}")
        return

    try:
        filename = f"contagem_{period.replace(':', '')}.csv"
        with open(filename, "w", newline='') as csvfile:
            fieldnames = ['Zona', 'Tipo de veículo', 'Período', 'Contagem']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for zone, vehicles in vehicle_counter.items():
                for vehicle_type, vehicle_set in vehicles.items():
                    writer.writerow({
                        'Zona': zone,
                        'Tipo de veículo': vehicle_type,
                        'Período': period,
                        'Contagem': len(vehicle_set)
                    })
        print(f"Vehicle counter written to {filename}")
    except Exception as e:
        print(f"An error occurred while writing to CSV: {e}")
    
if __name__ == '__main__':
    run_pipeline(sys.argv)