import os
import pickle
import logging

log = logging.getLogger(__name__)

import pandas as pd

import pycomm3
from l5x import l5x

import g
from global_keys import *


class LogixTags(object):
    TagDefinitionProperties = [
        'tag_name',
        # 'instance_id',
        'tag_type',
        # 'data_type',
        'data_type_name',
        # 'string',
        'external_access',
        # 'dim',
        # 'dimensions',
        'alias',
        # 'type_class',
    ]

    def __init__(self):
        self.all_tags_df = pd.DataFrame()
        self._cache_dir = os.path.join(g.project_config[PROJECT_PATH], "plc_cache")
        os.makedirs(self._cache_dir, exist_ok=True)  # Create cache directory if it doesn't exist
        log.debug(f"Cache dir = {self._cache_dir}")

    def _get_cache_file(self, plc_name: str):
        """Helper method to construct the cache file path."""
        return os.path.join(self._cache_dir, f"{plc_name}_tags.pkl")

    def save_cache(self, plc_name: str, plc_df: pd.DataFrame):
        """Saves the DataFrame to a cache file."""
        cache_file = self._get_cache_file(plc_name)
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(plc_df, f)
            log.debug(f"Cache file {cache_file} dumped")
        except (pickle.PickleError, EOFError, FileNotFoundError, FileExistsError, IsADirectoryError) as e:
            log.error(f"Cache file {cache_file} not saved: {e}")


    def load_cache(self, plc_name: str):
        """Loads the DataFrame from a cache file into self.all_tags_df"""
        cache_file = self._get_cache_file(plc_name)
        if os.path.exists(cache_file):
            log.info(f"Loading tags for '{plc_name}' from cache file: {cache_file}")
            try:
                with open(cache_file, 'rb') as f:
                    plc_df = pickle.load(f)
                    self.all_tags_df = pd.concat([self.all_tags_df, plc_df], ignore_index=True)
            except (pickle.PickleError, EOFError) as e:
                log.error(f"Error loading cache file: {e}")
        else:
            log.error(f"No cache file found for '{plc_name}'")
        return None  # Return None if loading fails

    def add_driver(self, plc_name: str, plc_communication_path: str):
        # cache_file = os.path.join(self._cache_dir, f"{plc_name}_tags.pkl")
        try:
            _driver = pycomm3.LogixDriver(plc_communication_path)
            _driver.open()

            tags_data = []
            for tag_name, tag_data in _driver.tags.items():
                tag_info = {'plc_name': plc_name, 'tag_name': tag_name}
                for prop in self.TagDefinitionProperties:
                    if prop in tag_data:
                        tag_info[prop] = tag_data[prop]
                tags_data.append(tag_info)

            # Create a DataFrame for the current PLC
            plc_df = pd.DataFrame(tags_data)
            _driver.close()

        except pycomm3.exceptions.CommError as e:
            log.warning(f"Failed to connect to PLC '{plc_name}'. Attempting to load from cache.")
            raise e

        # self.save_cache(plc_name, plc_df)
        # Concatenate with the main DataFrame (outside the try...except block)
        self.all_tags_df = pd.concat([self.all_tags_df, plc_df], ignore_index=True)

    # def add_driver(self, plc_name: str, new_driver: pycomm3.LogixDriver):
    #     cache_file = os.path.join(self._cache_dir, f"{plc_name}_tags.pkl")
    #
    #     try:
    #         if not new_driver.connected:
    #             new_driver.open()
    #
    #         tags_data = []
    #         for tag_name, tag_data in new_driver.tags.items():
    #             tag_info = {'plc_name': plc_name, 'tag_name': tag_name}
    #             for prop in self.TagDefinitionProperties:
    #                 if prop in tag_data:
    #                     tag_info[prop] = tag_data[prop]
    #             tags_data.append(tag_info)
    #
    #         # Create a DataFrame for the current PLC
    #         plc_df = pd.DataFrame(tags_data)
    #
    #         # Save DataFrame to cache file
    #         try:
    #             with open(cache_file, 'wb') as f:
    #                 pickle.dump(plc_df, f)
    #             log.debug(f"Cache file {cache_file} dumped")
    #         except (pickle.PickleError, EOFError, FileNotFoundError, FileExistsError, IsADirectoryError) as e:
    #             log.error(f"Cache file {cache_file} not saved")
    #             log.debug(f"{e}")
    #
    #
    #     except pycomm3.exceptions.CommError as e:
    #         log.warning(f"Failed to connect to PLC '{plc_name}'. Attempting to load from cache.")
    #         if os.path.exists(cache_file):
    #             log.info(f"Loading tags for '{plc_name}' from cache file: {cache_file}")
    #             try:
    #                 with open(cache_file, 'rb') as f:
    #                     plc_df = pickle.load(f)
    #             except (pickle.PickleError, EOFError) as e:
    #                 log.error(f"Error loading cache file: {e}. Skipping PLC '{plc_name}'.")
    #                 return
    #         else:
    #             log.error(f"No cache file found for '{plc_name}'")
    #             # raise e
    #             return
    #
    #     # Concatenate with the main DataFrame (outside the try...except block)
    #     self.all_tags_df = pd.concat([self.all_tags_df, plc_df], ignore_index=True)
    #
    #     if self.auto_close:
    #         new_driver.close()

    def add_l5x(self, plc_name: str, l5x_file_name: str):
        prj = l5x.Project(l5x_file_name)
        project_name = prj.doc.attrib['TargetName']
        log.info(F"Loading L5X file {l5x_file_name} ({project_name}) for PLC {plc_name}")

        # Create a dictionary to store base tag information
        base_tags = {}
        for tag_name in prj.controller.tags.names:
            try:
                tag_obj = prj.controller.tags[tag_name]
                try:
                    alias = tag_obj.alias_for
                    base_tags[tag_name] = alias  # Store tag_name as key and alias as value
                except AttributeError:
                    continue
            except RuntimeError:
                log.info(f"Skip {tag_name}")
                continue

        # Add the 'base_tag' column to the DataFrame
        self.all_tags_df['base_tag'] = self.all_tags_df.apply(
            lambda row: base_tags.get(row['tag_name']) if row['plc_name'] == plc_name else None,
            axis=1
        )

def __test__():
    lt = LogixTags()
    lt.add_driver('JAR', '11.110.58.10')
    print(lt.all_tags_df)


if __name__ == '__main__':
    __test__()
