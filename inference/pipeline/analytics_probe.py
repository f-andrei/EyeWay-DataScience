
import pyds # type: ignore
from inference.configs.constants import *
from gi.repository import GLib, Gst # type: ignore

def nvanalytics_src_pad_buffer_probe(pad, info, u_data):
    people_count = 0
    frame_number=0
    num_rects=0
    gst_buffer = info.get_buffer()
    if not gst_buffer:
        print("Unable to get GstBuffer ")
        return

    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
    l_frame = batch_meta.frame_meta_list

    while l_frame:
        try:
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        except StopIteration:
            break

        frame_number=frame_meta.frame_num
        l_obj=frame_meta.obj_meta_list
        num_rects = frame_meta.num_obj_meta
        is_first_obj = True
        save_image = False
        obj_counter = {
        PGIE_CLASS_ID_VEHICLE:0,
        PGIE_CLASS_ID_PERSON:0,
        PGIE_CLASS_ID_BICYCLE:0,
        PGIE_CLASS_ID_ROADSIGN:0
        }

        while l_obj:
            try: 
                obj_meta=pyds.NvDsObjectMeta.cast(l_obj.data)
            except StopIteration:
                break

            l_user_meta = obj_meta.obj_user_meta_list
            # Extract object level meta data from NvDsAnalyticsObjInfo
            while l_user_meta:
                try:
                    user_meta = pyds.NvDsUserMeta.cast(l_user_meta.data)
                    if user_meta.base_meta.meta_type == pyds.nvds_get_user_meta_type("NVIDIA.DSANALYTICSOBJ.USER_META"):             
                        user_meta_data = pyds.NvDsAnalyticsObjInfo.cast(user_meta.user_meta_data)                  
                        if user_meta_data.lcStatus: 
                            # print(user_meta_data.unique_id)
                            ...
                except StopIteration:
                    break

                try:
                    l_user_meta = l_user_meta.next
                except StopIteration:
                    break
            try: 
                l_obj=l_obj.next
            except StopIteration:
                break

        
        # Get meta data from NvDsAnalyticsFrameMeta
        l_user = frame_meta.frame_user_meta_list
        while l_user:
            try:
                user_meta = pyds.NvDsUserMeta.cast(l_user.data)
                if user_meta.base_meta.meta_type == pyds.nvds_get_user_meta_type("NVIDIA.DSANALYTICSFRAME.USER_META"):
                    user_meta_data = pyds.NvDsAnalyticsFrameMeta.cast(user_meta.user_meta_data)
            except StopIteration:
                break
            try:
                l_user = l_user.next
            except StopIteration:
                break
        
        display_meta=pyds.nvds_acquire_display_meta_from_pool(batch_meta)
        display_meta.num_labels = 1
        py_nvosd_text_params = display_meta.text_params[0]

        total_vehicles = sum([
            user_meta_data.objLCCumCnt["left-lane"], 
            user_meta_data.objLCCumCnt["middle-lane"], 
            user_meta_data.objLCCumCnt["right-lane"]
            ])
        
        people_count = sum([
            user_meta_data.objLCCumCnt["sidewalk-left-up"],
            user_meta_data.objLCCumCnt["sidewalk-left-down"],
            user_meta_data.objLCCumCnt["sidewalk-right-up"],
            user_meta_data.objLCCumCnt["sidewalk-right-down"]
        ])
        py_nvosd_text_params.display_text = "Total vehicles: {} People count: {}".format(total_vehicles, people_count)

        py_nvosd_text_params.x_offset = 10
        py_nvosd_text_params.y_offset = 12

        py_nvosd_text_params.font_params.font_name = "Serif"
        py_nvosd_text_params.font_params.font_size = 15

        py_nvosd_text_params.font_params.font_color.set(0, 1.0, 1.0, 1.0)

        py_nvosd_text_params.set_bg_clr = 1

        py_nvosd_text_params.text_bg_clr.set(0.0, 0.0, 0.0, 1.0)
        pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)
        # stream_index = "stream{0}".format(frame_meta.pad_index)
        # global perf_data
        # perf_data.update_fps(stream_index)


        try:
            l_frame=l_frame.next
        except StopIteration:
            break

    return Gst.PadProbeReturn.OK
