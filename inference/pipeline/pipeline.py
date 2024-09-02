import sys
import gi # type: ignore
from .element_links import link_elements
from .elements import get_elements
from .properties import set_output_properties, set_pgie_properties, set_streammux_properties, set_tiler_properties, set_tracker_properties
gi.require_version('Gst', '1.0')
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
    print("In cb_newpad\n")
    caps=decoder_src_pad.get_current_caps()
    if not caps:
        caps = decoder_src_pad.query_caps()
    gststruct=caps.get_structure(0)
    gstname=gststruct.get_name()
    source_bin=data
    features=caps.get_features(0)

    # Need to check if the pad created by the decodebin is for video and not
    # audio.
    print("gstname=",gstname)
    if(gstname.find("video")!=-1):
        print("features=",features)
        if features.contains("memory:NVMM"):
            # Get the source bin ghost pad
            bin_ghost_pad=source_bin.get_static_pad("src")
            if not bin_ghost_pad.set_target(decoder_src_pad):
                sys.stderr.write("Failed to link decoder src pad to source bin ghost pad\n")
        else:
            sys.stderr.write(" Error: Decodebin did not pick nvidia decoder plugin.\n")

def decodebin_child_added(child_proxy, Object, name, user_data):
    print("Decodebin child added:", name, "\n")
    if name.find("decodebin") != -1:
        Object.connect("child-added", decodebin_child_added, user_data)

    if not platform_info.is_integrated_gpu() and name.find("nvv4l2decoder") != -1:
        Object.set_property("cudadec-memtype", 2)

    if "source" in name:
        source_element = child_proxy.get_by_name("source")
        if source_element.find_property('drop-on-latency') != None:
            Object.set_property("drop-on-latency", True)

def create_source_bin(index, uri):
    print("Creating source bin")

    bin_name="source-bin-%02d" %index
    print(bin_name)
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
    factory.set_protocols(GstRtsp.RTSPLowerTrans.TCP)
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
        print("Creating nv3dsink \n")
        sink = Gst.ElementFactory.make("nv3dsink", "nv3d-sink")
        if not sink:
            sys.stderr.write(" Unable to create nv3dsink \n")
    else:
        if platform_info.is_platform_aarch64():
            print("Creating nv3dsink \n")
            sink = Gst.ElementFactory.make("nv3dsink", "nv3d-sink")
        else:
            print("Creating EGLSink \n")
            sink = Gst.ElementFactory.make("nveglglessink", "nvvideo-renderer")
        if not sink:
            sys.stderr.write(" Unable to create egl sink \n")



    config = configparser.ConfigParser()
    config.read(TRACKER_CONFIG_FILE)
    config.sections()

    config, elements = set_tracker_properties(config, elements)
    
    elements["nvdsanalytics"].set_property("config-file", ANALYTICS_CONFIG_FILE)

    tiler = set_tiler_properties(elements, number_sources)

    sink.set_property("qos", 0)

    caps1 = Gst.Caps.from_string("video/x-raw(memory:NVMM), format=RGBA")
    elements["filter1"].set_property("caps", caps1)
    if not platform_info.is_integrated_gpu():
        # Use CUDA unified memory in the pipeline so frames
        # can be easily accessed on CPU in Python.
        vc_mem_type = int(pyds.NVBUF_MEM_CUDA_PINNED)
        mem_type = int(pyds.NVBUF_MEM_CUDA_UNIFIED)
        elements["streammux"].set_property("nvbuf-memory-type", vc_mem_type)
        elements["nvvidconv"].set_property("nvbuf-memory-type", mem_type)
        if platform_info.is_wsl():
            #opencv functions like cv2.line and cv2.putText is not able to access NVBUF_MEM_CUDA_UNIFIED memory
            #in WSL systems due to some reason and gives SEGFAULT. Use NVBUF_MEM_CUDA_PINNED memory for such
            #usecases in WSL. Here, nvvidconv1's buffer is used in tiler sink pad probe and cv2 operations are
            #done on that.
            vc_vc_mem_type = int(pyds.NVBUF_MEM_CUDA_PINNED)
            print("using nvbuf_mem_cuda_pinned memory for nvvidconv1\n", vc_mem_type)
            elements["nvvidconv1"].set_property("nvbuf-memory-type", vc_mem_type)
        else:
            elements["nvvidconv1"].set_property("nvbuf-memory-type", vc_mem_type)
        tiler.set_property("nvbuf-memory-type", vc_mem_type)
    streammux = set_streammux_properties(elements)

    set_pgie_properties(elements, number_sources)
    set_output_properties(elements, stream_output, number_sources)

    for element in elements.values():
        pipeline.add(element)


    for i in range(number_sources):
        print("Creating source_bin ", i, " \n ")
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