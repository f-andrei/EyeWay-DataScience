import requests # type: ignore
import os

def generate_nvdsanalytics_config_file(camera_name):
    try:
        # Fetch camera data from API
        response = requests.get(f"http://172.26.144.1:3000/cameras-line-pairs/{camera_name}")
        response.raise_for_status()
        camera_data = response.json()

        # Create config directory if it doesn't exist
        config_dir = '/opt/nvidia/deepstream/deepstream-7.0/sources/apps/inference/configs'
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        # Generate config file content
        config_content = []

        # Add property section
        config_content.extend([
            '[property]',
            'enable=1',
            f'config-width={camera_data["imageSize"]["width"]}',
            f'config-height={camera_data["imageSize"]["height"]}',
            'osd-mode=2',
            'display-font-size=12',
            ''
        ])

        # Add ROI section if ROIs exist
        if camera_data.get('rois'):
            config_content.extend([
                '[roi-filtering-stream-0]',
                'enable=1',
                ''
            ])
            
            # Process ROIs
            for idx, roi in enumerate(camera_data['rois']):
                roi_points = '; '.join([f"{point['x']};{point['y']}" for point in roi])
                config_content.append(f'# Region {idx} polygon')
                config_content.append(f'roi-{idx} = {roi_points}')
                config_content.append('')

        # Add line crossing section if line pairs exist
        if camera_data.get('linePairs'):
            config_content.extend([
                '[line-crossing-stream-0]',
                'enable=1',
                ''
            ])
            
            # Process line pairs
            for idx, pair in enumerate(camera_data['linePairs']):
                # Format direction line coordinates
                direction_line = pair['direction']
                direction_points = f"{direction_line[0]['x']};{direction_line[0]['y']}; " \
                                f"{direction_line[1]['x']};{direction_line[1]['y']}"

                # Format crossing line coordinates
                crossing_line = pair['crossing']
                crossing_points = f"{crossing_line[0]['x']};{crossing_line[0]['y']}; " \
                                f"{crossing_line[1]['x']};{crossing_line[1]['y']}"

                # Get line type identifier (C for Contagem, P for Conversão proibida)
                type_id = 'contagem' if pair['type'] == 'Contagem' else 'conversao-proibida'

                # Add line configuration
                config_content.append(f'# Line crossing {idx} - {pair["type"]}')
                config_content.append(f'line-crossing-{type_id}-{idx} = {direction_points}; {crossing_points}')
                config_content.append('')

        # Add mode at the end
        config_content.append('mode=balanced')

        # Write to file
        config_file_path = os.path.join(config_dir, f'{camera_name}_config.txt')
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