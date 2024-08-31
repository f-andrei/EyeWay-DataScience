

def link_elements(elements, sink):
    elements["streammux"].link(elements["nvdspreprocess"])
    elements["nvmultiurisrcbin"].link(elements["nvdspreprocess"])
    elements["pgie"].link(elements["nvvidconv"])
    elements["nvvidconv"].link(elements["filter1"])
    elements["filter1"].link(elements["nvtracker"])
    elements["nvtracker"].link(elements["nvdsanalytics"])
    elements["nvdsanalytics"].link(elements["nvtiler"])
    elements["nvtiler"].link(elements["nvvidconv2"])
    elements["nvvidconv2"].link(elements["nvosd"])
    elements["nvosd"].link(sink)

    return elements