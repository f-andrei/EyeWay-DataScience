from utils.constants import BACKEND_API_URL
import requests # type: ignore
import os

def generate_nvdsanalytics_config_file(camera_name):
    try:
        response = requests.get(f"{BACKEND_API_URL}/cameras-line-pairs/{camera_name}")
        response.raise_for_status()
        camera_data = response.json()

        config_dir = '/apps/inference/configs/nvdsanalytics'
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        config_content = []

        width = camera_data["imageSize"]["width"]
        height = camera_data["imageSize"]["height"]

        config_content.extend([
            '[property]',
            'enable=1',
            f'config-width={width}',
            f'config-height={height}',
            'osd-mode=2',
            'display-font-size=12',
            '',
            '[direction-detection-stream-0]',
            'enable=1',
            '',
            f'direction-Sul={width//2};{height//2};{width//2};{0}',
            f'direction-Norte={width//2};{height//2};{width//2};{height}',
            f'direction-Leste={width//2};{height//2};{width};{height//2}',
            f'direction-Oeste={width//2};{height//2};{0};{height//2}',

            '',
            '',
        ])

        if camera_data.get('rois'):
            config_content.extend([
                '[roi-filtering-stream-0]',
                'enable=1',
                ''
            ])
            
            for idx, roi in enumerate(camera_data['rois']):
                roi_points = '; '.join([f"{point['x']};{point['y']}" for point in roi['points']])
                roi_type = "presence" if roi['type'] == "Presença" else "intersection"
                config_content.append(f'# Region {idx} polygon')
                config_content.append(f'roi-{roi_type}-{idx}={roi_points}')
                config_content.append('')

        if camera_data.get('linePairs'):
            config_content.extend([
                '[line-crossing-stream-0]',
                'enable=1',
                ''
            ])
            
            for idx, pair in enumerate(camera_data['linePairs']):
                direction_line = pair['direction']
                direction_points = f"{direction_line[0]['x']};{direction_line[0]['y']}; " \
                                f"{direction_line[1]['x']};{direction_line[1]['y']}"

                crossing_line = pair['crossing']
                crossing_points = f"{crossing_line[0]['x']};{crossing_line[0]['y']}; " \
                                f"{crossing_line[1]['x']};{crossing_line[1]['y']}"
                lc_type = "counter" if pair['type'] == "Contagem" else "u-turn"
  
                config_content.append(f'# Line crossing {idx} - {pair["type"]}')
                config_content.append(f'line-crossing-{lc_type}-{idx} = {direction_points}; {crossing_points}')
                config_content.append('')

            config_content.append('mode=balanced')


        config_file_path = os.path.join(config_dir, f'{camera_name}_nvdsanalytics.txt')
        with open(config_file_path, 'w') as f:
            f.write('\n'.join(config_content))

        print(f"Configuration file generated successfully: {config_file_path}")
        return config_file_path

    except requests.exceptions.RequestException as e:
        print(f"Error fetching camera data: {e}")
        return False
    except Exception as e:
        print(f"Error generating config file: {e}")
        return False