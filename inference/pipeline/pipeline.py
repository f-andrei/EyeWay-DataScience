import sys
import gi # type: ignore
from .element_links import link_elements
from .elements import get_elements
from .properties import set_output_properties, set_pgie_properties, set_streammux_properties, set_tiler_properties, set_tracker_properties
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GstRtsp # type: ignore
from common.platform_info import PlatformInfo
from common.FPS import PERF_DATA
import configparser
from configs.constants import *
import pyds # type: ignore


frame_count = {}
saved_count = {}
perf_data = None


def cb_newpad(decodebin, decoder_src_pad,data):
    caps=decoder_src_pad.get_current_caps()
    if not caps:
        caps = decoder_src_pad.query_caps()
    gststruct=caps.get_structure(0)
    gstname=gststruct.get_name()
    source_bin=data
    features=caps.get_features(0)

    # Need to check if the pad created by the decodebin is for video and not
    # audio.
    if(gstname.find("video")!=-1):
        if features.contains("memory:NVMM"):
            # Get the source bin ghost pad
            bin_ghost_pad=source_bin.get_static_pad("src")
            if not bin_ghost_pad.set_target(decoder_src_pad):
                sys.stderr.write("Failed to link decoder src pad to source bin ghost pad\n")
        else:
            sys.stderr.write(" Error: Decodebin did not pick nvidia decoder plugin.\n")

def decodebin_child_added(child_proxy, Object, name, user_data):
    if name.find("decodebin") != -1:
        Object.connect("child-added", decodebin_child_added, user_data)

    if not platform_info.is_integrated_gpu() and name.find("nvv4l2decoder") != -1:
        Object.set_property("cudadec-memtype", 2)

    if "source" in name:
        source_element = child_proxy.get_by_name("source")
        if source_element.find_property('drop-on-latency') != None:
            Object.set_property("drop-on-latency", True)

def create_source_bin(index, uri):
    bin_name="source-bin-%02d" %index
    nbin=Gst.Bin.new(bin_name)
    if not nbin:
        sys.stderr.write(" Unable to create source bin \n")

    uri_decode_bin=Gst.ElementFactory.make("nvurisrcbin", "uri-decode-bin")
    if not uri_decode_bin:
        sys.stderr.write(" Unable to create uri decode bin \n")
    
    uri_decode_bin.set_property("uri", uri)
    uri_decode_bin.connect("pad-added", cb_newpad, nbin)
    uri_decode_bin.connect("child-added", decodebin_child_added, nbin)

    Gst.Bin.add(nbin,uri_decode_bin)
    bin_pad=nbin.add_pad(Gst.GhostPad.new_no_target("src",Gst.PadDirection.SRC))
    if not bin_pad:
        sys.stderr.write(" Failed to add ghost pad in source bin \n")
        return None
    return nbin

def create_rtsp_server():
    rtsp_port_num = 8554
    rtsp_stream_end = "/live"
    username =  'user'
    password =  "pass"
    updsink_port_num = 8245
    codec = 'H264'

    server = GstRtspServer.RTSPServer.new()
    server.props.service = "%d" % rtsp_port_num
    server.attach(None)

    factory = GstRtspServer.RTSPMediaFactory.new()
    factory.set_protocols(GstRtsp.RTSPLowerTrans.UDP)
    factory.set_transport_mode(GstRtspServer.RTSPTransportMode.PLAY)
    factory.set_latency(1)
    factory.set_launch(
        '( udpsrc name=pay0  port=%d buffer-size=10485760  caps="application/x-rtp, media=video, clock-rate=90000, mtu=1300, encoding-name=(string)%s, payload=96 " )'
        % (updsink_port_num, codec)
    )
    factory.set_shared(True)
    permissions = GstRtspServer.RTSPPermissions()
    permissions.add_permission_for_role(username, "media.factory.access", True)
    permissions.add_permission_for_role(username, "media.factory.construct", True)
    factory.set_permissions(permissions)
    server.get_mount_points().add_factory(rtsp_stream_end, factory)
    print("\n Transmissão rtsp inicializada em: rtsp://%s:%s@%s:%d%s \n\n" %
        (username, password, 'localhost', rtsp_port_num, rtsp_stream_end))

# Function to create the pipeline
def create_pipeline(args):
    stream_output = args.output

    global platform_info
    platform_info = PlatformInfo()
    
    number_sources=len(args.input)
    
    global perf_data
    perf_data = PERF_DATA(len(args.input))

    Gst.init(None)
    
    pipeline = Gst.Pipeline()
    if not pipeline:
        sys.stderr.write("Unable to create Pipeline\n")
        return None

    elements = get_elements(args.output)
    for name, val in elements.items():
        element = Gst.ElementFactory.make(val[0], val[1])
        if not element:
            sys.stderr.write(f"Unable to create {name}\n")
            return None
        elements[name] = element

    if platform_info.is_integrated_gpu():
        sink = Gst.ElementFactory.make("nv3dsink", "nv3d-sink")
        if not sink:
            sys.stderr.write(" Unable to create nv3dsink \n")
    else:
        if platform_info.is_platform_aarch64():
            sink = Gst.ElementFactory.make("nv3dsink", "nv3d-sink")
        # else:
        #     sink = Gst.ElementFactory.make("nveglglessink", "nvvideo-renderer")
        # if not sink:
        #     sys.stderr.write(" Unable to create egl sink \n")

        else:
            sink = Gst.ElementFactory.make("fakesink", "fakesink")

    config = configparser.ConfigParser()
    config.read(TRACKER_CONFIG_FILE)
    config.sections()

    config, elements = set_tracker_properties(config, elements)
    
    elements["nvdsanalytics"].set_property("config-file", ANALYTICS_CONFIG_FILE)

    if stream_output != "none":
        tiler = set_tiler_properties(elements, number_sources)
    else:
        tiler = None
    sink.set_property("qos", 0)
    caps1 = Gst.Caps.from_string("video/x-raw(memory:NVMM), format=RGBA")
    elements["filter_analytics"].set_property("caps", caps1)
    streammux = set_streammux_properties(elements)

    set_pgie_properties(elements, number_sources)
    filename = args.input[0].split(".")[0].split("/")[-1]

    set_output_properties(elements, stream_output, number_sources, filename)

    for element in elements.values():
        pipeline.add(element)


    for i in range(number_sources):
        uri_name = args.input[i]
        if uri_name.find("rtsp://") == 0:
            is_live = True
        source_bin = create_source_bin(i, uri_name)
        if not source_bin:
            sys.stderr.write("Unable to create source bin \n")
        pipeline.add(source_bin)
        padname = "sink_%u" % i
        sinkpad = streammux.request_pad_simple(padname)
        if not sinkpad:
            sys.stderr.write("Unable to create sink pad bin \n")
        srcpad = source_bin.get_static_pad("src")
        if not srcpad:
            sys.stderr.write("Unable to create src pad bin \n")
        srcpad.link(sinkpad)

    elements, element_probe = link_elements(elements, stream_output)

    return pipeline, elements["nvdsanalytics"], perf_data, element_probe