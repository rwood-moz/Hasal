import os
import sys
import json
import time
from lib.common.logConfig import get_logger
from lib.common.commonUtil import NetworkUtil
from lib.common.commonUtil import CommonUtil
from archiveMozillaHelper import ArchiveMozillaHelper
from perfherderDataQueryHelper import PerfherderDataQueryHelper


logger = get_logger(__name__)


class GenerateBackfillTableHelper(object):
    DEFAULT_HG_QUERY_REVISION_JSON_URL = 'https://hg.mozilla.org/mozilla-central/json-rev'
    DEFAULT_BACKFILL_TABLE_LOCAL_FN = 'backfill_table.json'
    PLATFORM_BACKFILL_TABLE_LOCAL_FN = 'backfill_table_{platform}.json'

    @staticmethod
    def generate_archive_revision_relation_table(input_history_backfill_table, input_backfill_days=14, input_backfill_repo="mozilla-central", input_app_name="firefox", input_channel_name="nightly", input_platform=None):
        """
        generate archive dir and revision relation table.

        @param input_history_backfill_table:
        @param input_backfill_days:
        @param input_backfill_repo:
        @param input_app_name:
        @param input_channel_name:
        @param input_platform: only accept string value of  "linux64", "mac", "win64"
        @return: dict object, example::
            {
            1505812350: {'pkg_json_url': u'https://archive.mozilla.org/pub/firefox/nightly/2017/09/2017-09-19-10-04-05-mozilla-central/firefox-57.0a1.en-US.mac.json',
                         'pkg_fn_url': u'https://archive.mozilla.org/pub/firefox/nightly/2017/09/2017-09-19-10-04-05-mozilla-central/firefox-57.0a1.en-US.mac.dmg',
                         'revision': u'e4261f5b96ebfd63e7cb8af3035ff9fea90c74a5'}
            }

        """
        archieve_revision_relation_table = {}
        backfill_repo_name = input_backfill_repo + "/"
        history_backfill_url_dict = {}
        history_backfill_dir_list = []

        # init platform value
        if input_platform:
            current_platform_for_archive = input_platform
        else:
            if sys.platform == "linux2":
                current_platform_for_archive = "linux64"
            elif sys.platform == "darwin":
                current_platform_for_archive = "mac"
            else:
                current_platform_for_archive = "win64"

        # generate history backfill dir list
        # convert history data into backfill_url_dict
        for data_timestamp in input_history_backfill_table.keys():
            history_archive_dir = input_history_backfill_table[data_timestamp].get("archive_dir", None)
            history_archive_url = input_history_backfill_table[data_timestamp].get("archive_url", None)
            history_archive_datetime = input_history_backfill_table[data_timestamp].get("archive_datetime", None)
            history_revsison = input_history_backfill_table[data_timestamp].get("revision", None)
            history_pkg_json_url = input_history_backfill_table[data_timestamp].get("pkg_json_url", None)
            history_pkg_fn_url = input_history_backfill_table[data_timestamp].get("pkg_fn_url", None)

            if history_archive_dir and history_archive_url:
                history_backfill_dir_list.append(history_archive_dir)
                history_backfill_url_dict[history_archive_url] = {"revision": history_revsison,
                                                                  "pkg_json_url": history_pkg_json_url,
                                                                  "pkg_fn_url": history_pkg_fn_url,
                                                                  "archive_url": history_archive_url,
                                                                  "archive_dir": history_archive_dir,
                                                                  "archive_datetime": history_archive_datetime,
                                                                  "push_date_stamp": data_timestamp}

        total_backfill_url_dict = ArchiveMozillaHelper.get_backfill_folder_dict(input_backfill_days, backfill_repo_name, input_app_name, input_channel_name, history_backfill_dir_list)
        for current_backfill_dir_url in total_backfill_url_dict.keys():

            # get fx pkg revison
            if current_backfill_dir_url not in history_backfill_url_dict:
                current_backfill_fx_pkg_fn, current_backfill_fx_pkg_json = ArchiveMozillaHelper.get_fx_pkg_name(current_platform_for_archive, current_backfill_dir_url)
                if current_backfill_fx_pkg_fn and current_backfill_fx_pkg_json:
                    current_backfill_fx_pkg_fn_url = ArchiveMozillaHelper.DEFAULT_ARCHIVE_URL + current_backfill_fx_pkg_fn
                    current_backfill_fx_pkg_json_url = ArchiveMozillaHelper.DEFAULT_ARCHIVE_URL + current_backfill_fx_pkg_json
                    current_backfill_fx_pkg_json_response = NetworkUtil.get_request_and_response(current_backfill_fx_pkg_json_url)
                    if current_backfill_fx_pkg_json_response:
                        current_backfill_fx_pkg_json_obj = current_backfill_fx_pkg_json_response.json()
                        current_backfill_revision = current_backfill_fx_pkg_json_obj.get("moz_source_stamp", None)
                        if current_backfill_revision:

                            # get fx pkg push date
                            query_hg_json_url = "%s/%s" % (GenerateBackfillTableHelper.DEFAULT_HG_QUERY_REVISION_JSON_URL, current_backfill_revision)
                            query_hg_json_response = NetworkUtil.get_request_and_response(query_hg_json_url)
                            if query_hg_json_response:
                                query_hg_json_obj = query_hg_json_response.json()

                                # the existing data example looks like [1505857765, 0]
                                # not sure what do we need to do with second value, skip handling it first

                                # should modify from integer to string
                                current_backfill_revision_push_date_stamp = str(query_hg_json_obj.get("pushdate", None)[0])

                                if current_backfill_revision_push_date_stamp:
                                    archieve_revision_relation_table[current_backfill_revision_push_date_stamp] = {"revision": current_backfill_revision,
                                                                                                                   "pkg_json_url": current_backfill_fx_pkg_json_url,
                                                                                                                   "pkg_fn_url": current_backfill_fx_pkg_fn_url,
                                                                                                                   "archive_url": current_backfill_dir_url,
                                                                                                                   "archive_dir": total_backfill_url_dict[current_backfill_dir_url]['folder_name'],
                                                                                                                   "archive_datetime": total_backfill_url_dict[current_backfill_dir_url]['folder_datetime']}
                                else:
                                    logger.error("Cannot get corresponding datetime from pushdate key from json obj [%s]" % query_hg_json_obj)
                            else:
                                logger.error("Cannot get corresponding hg revision json content from url : [%s]" % query_hg_json_url)
                        else:
                            logger.error("Cannot get corresponding revision from moz_source_stamp key from json obj [%s]" % current_backfill_fx_pkg_json_obj)
                    else:
                        logger.error("Cannot get corresponding fx pkg json file content from url : [%s]" % current_backfill_fx_pkg_json_url)
                else:
                    logger.error("Cannot get reference fx pkg fn and json fn from archive folder")
            else:
                archieve_revision_relation_table[history_backfill_url_dict[current_backfill_dir_url]["push_date_stamp"]] = {
                    "revision": history_backfill_url_dict[current_backfill_dir_url]["revision"],
                    "pkg_json_url": history_backfill_url_dict[current_backfill_dir_url]["pkg_json_url"],
                    "pkg_fn_url": history_backfill_url_dict[current_backfill_dir_url]["pkg_fn_url"],
                    "archive_url": current_backfill_dir_url,
                    "archive_dir": history_backfill_url_dict[current_backfill_dir_url]["archive_dir"],
                    "archive_datetime": history_backfill_url_dict[current_backfill_dir_url]["archive_datetime"]}

        return archieve_revision_relation_table

    @staticmethod
    def generate_archive_perfherder_relational_table(input_backfill_days=14, input_backfill_repo="mozilla-central", input_app_name="firefox", input_channel_name="nightly", input_white_list=[], input_platform=None):
        """
        (I AM THE ENTRY POINT!!!) You can call me to generate the big archive-revision-perfherder releation table
        @param input_backfill_days:
        @param input_backfill_repo:
        @param input_app_name:
        @param input_channel_name:
        @param input_white_list:
        @param input_platform: only accept string value of  "linux64", "mac", "win64"
        @return:
        """

        # load existing backfill table data
        history_backfill_table = {}
        if input_platform:
            backfile_table_file = GenerateBackfillTableHelper.PLATFORM_BACKFILL_TABLE_LOCAL_FN.format(platform=input_platform)
        else:
            backfile_table_file = GenerateBackfillTableHelper.DEFAULT_BACKFILL_TABLE_LOCAL_FN

        if os.path.exists(backfile_table_file):
            with open(backfile_table_file) as read_fh:
                history_backfill_table = json.load(read_fh)

        # get archive and revision mapping table data
        current_archive_data_table = GenerateBackfillTableHelper.generate_archive_revision_relation_table(history_backfill_table, input_backfill_days, input_backfill_repo, input_app_name, input_channel_name, input_platform)

        # get archive and perfherder mapping table data
        current_perfherder_data_table = PerfherderDataQueryHelper.get_perfherder_data(input_white_list=input_white_list, input_query_days=input_backfill_days, input_query_channel=input_backfill_repo)

        # merge data
        result_data = CommonUtil.deep_merge_dict(current_archive_data_table, current_perfherder_data_table)

        with open(backfile_table_file, "w") as write_fh:
            json.dump(result_data, write_fh)

        return result_data

    @staticmethod
    def get_history_archive_perfherder_relational_table(input_platform=None):
        """
        adding a method for reading history_backfill_table, and return a dict object, which has while loop for try/catch of error handling.
        @param input_platform: only accept string value of  "linux64", "mac", "win64"
        @return:
        """
        if input_platform:
            backfill_table_file = GenerateBackfillTableHelper.PLATFORM_BACKFILL_TABLE_LOCAL_FN.format(platform=input_platform)
        else:
            backfill_table_file = GenerateBackfillTableHelper.DEFAULT_BACKFILL_TABLE_LOCAL_FN

        history_backfill_table = {}
        if os.path.exists(backfill_table_file):
            for _ in range(10):
                try:
                    with open(backfill_table_file) as read_fh:
                        history_backfill_table = json.load(read_fh)
                        break
                except:
                    time.sleep(0.5)

        return history_backfill_table
