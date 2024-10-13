def link_elements(elements, stream_output):
    if stream_output == "none":
        element_probe = elements["queue"]
        elements["streammux"].link(elements["pgie"])
        elements["pgie"].link(elements["nvvidconv1"])
        elements["nvvidconv1"].link(elements["filter1"])
        elements["filter1"].link(elements["nvtracker"])
        elements["nvtracker"].link(elements["nvdsanalytics"])
        elements["nvdsanalytics"].link(elements["queue"])
        elements["queue"].link(elements["sink"])

    if stream_output in ("file", "rtsp", "display"):
        element_probe = elements["nvtiler"]
        elements["streammux"].link(elements["pgie"])
        elements["pgie"].link(elements["nvvidconv1"])
        elements["nvvidconv1"].link(elements["filter1"])
        elements["filter1"].link(elements["nvtracker"])
        elements["nvtracker"].link(elements["nvdsanalytics"])
        elements["nvdsanalytics"].link(elements["nvtiler"])
        elements["nvtiler"].link(elements["nvvidconv"])
        elements["nvvidconv"].link(elements["nvosd"])
        if stream_output in ("file", "rtsp"):
            elements["nvosd"].link(elements["nvvidconv_encoder"])
            elements["nvvidconv_encoder"].link(elements["filter_encoder"])
            elements["filter_encoder"].link(elements["encoder"])
            if stream_output == "file":
                elements["encoder"].link(elements["codeparser"])
                elements["codeparser"].link(elements["container"])
                elements["container"].link(elements["sink"])
            if stream_output == "rtsp":
                elements["encoder"].link(elements["rtppay"])
                elements["rtppay"].link(elements["sink"])
        
        else:
            elements["nvosd"].link(elements["sink"])


    return elements, element_probe