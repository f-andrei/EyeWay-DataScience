import pyds # type: ignore
from configs.constants import *
import gi # type: ignore
gi.require_version('Gst', '1.0') # type: ignore
from gi.repository import Gst # type: ignore
import cv2 # type: ignore
import numpy as np # type: ignore
from common.platform_info import PlatformInfo
platform_info = PlatformInfo()
saved_objects = {}
from common.send_to_db import InfractionsHandler
import csv

infraction_handler = InfractionsHandler()


def nvanalytics_src_pad_buffer_probe(pad, info, u_data, perf_data, vehicle_counter):
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
                print("l_user_meta")
                try:
                    user_meta = pyds.NvDsUserMeta.cast(l_user_meta.data)
                    if user_meta.base_meta.meta_type == pyds.nvds_get_user_meta_type("NVIDIA.DSANALYTICSOBJ.USER_META"):  
                        user_meta_data = pyds.NvDsAnalyticsObjInfo.cast(user_meta.user_meta_data)                  
                        print("user_meta_data")
                        if user_meta_data.lcStatus:
                            print("LC")
                            class_id = obj_meta.class_id
                            obj_id = obj_meta.object_id
                            line_crossing_name = user_meta_data.lcStatus[0].strip()
                            if class_id == 2:
                                print("aqui")
                                vehicle_counter[line_crossing_name]["Carro"].add(obj_id)
                            elif class_id == 3:
                                print("aqui")
                                vehicle_counter[line_crossing_name]["Moto"].add(obj_id)
                            elif class_id == 5:
                                print("aqui")
                                vehicle_counter[line_crossing_name]["Onibus"].add(obj_id)
                            elif class_id ==7:
                                print("aqui")
                                vehicle_counter[line_crossing_name]["Caminhao"].add(obj_id)
                            print(vehicle_counter)
                            print(f"G1: {[(key, len(value)) for key, value in vehicle_counter['G1'].items()]}")
                            print(f"G2: {[(key, len(value)) for key, value in vehicle_counter['G2'].items()]}")
                            print(f"G3: {[(key, len(value)) for key, value in vehicle_counter['G3'].items()]}")
                            # infraction_type = "Conversao proibida"
                            # print("Conversão proibida detectada") 
                            # infraction_handler.handle_infraction(gst_buffer, frame_meta, obj_meta, infraction_type)
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


