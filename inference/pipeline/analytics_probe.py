import pyds # type: ignore
from configs.constants import *
import gi # type: ignore
gi.require_version('Gst', '1.0') # type: ignore
from gi.repository import Gst # type: ignore
from common.platform_info import PlatformInfo
platform_info = PlatformInfo()
saved_objects = {}
from common.send_to_db import InfractionsHandler, ObjectCounter

infraction_handler = InfractionsHandler()
object_counter = ObjectCounter()

def nvanalytics_src_pad_buffer_probe(pad, info, u_data, perf_data, camera_id):
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
        
        l_obj=frame_meta.obj_meta_list


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
                            line_crossing_names = user_meta_data.lcStatus
                            for lc in line_crossing_names:
                                if lc.startswith("conversao-proibida") and obj_meta.class_id in [2, 3, 5, 7]:
                                    infraction_type = "Conversão proibida"
                                    print("Conversão proibida detectada") 
                                    infraction_handler.handle_infraction(gst_buffer, frame_meta, obj_meta, infraction_type, camera_id)
                                if lc.startswith("contagem") and obj_meta.class_id in [0, 1, 2, 3, 5, 7]:
                                    object_counter.count_objects(obj_meta, camera_id)
                
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
        
     
        stream_index = "stream{0}".format(frame_meta.pad_index)
        perf_data.update_fps(stream_index)


        try:
            l_frame=l_frame.next
        except StopIteration:
            break
        
    return Gst.PadProbeReturn.OK


