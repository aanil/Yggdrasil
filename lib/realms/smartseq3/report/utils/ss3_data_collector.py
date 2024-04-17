import pandas as pd
import loompy as lp
import numpy as np

# import time
from pandas.errors import EmptyDataError

from lib.utils.logging_utils import custom_logger

logging = custom_logger(__name__.split('.')[-1])

class SS3DataCollector:
    def __init__(self, output_handler, sample):
        """
        Initialize the data collector with a reference to an instance of zUMIsOutputHandler.

        Args:
            output_handler (zUMIsOutputHandler): An instance of zUMIsOutputHandler.
        """
        self.sample = sample
        self.output_handler = output_handler
        self.meta = self.sample.metadata
        self.config = self.sample.config

    # def collect_stats(self):
    #     barcode_set = self.meta.get('barcode_set')
    #     if not barcode_set:
    #         logging.error("Missing barcode_set in metadata. Unable to extract well IDs.")
    #         # TODO: (FUTURE) Develope an exception handling strategy and raise an exception here (FUTURE)
    #         return None  # Or raise an exception, depending on your error handling strategy

    #     # get well_ids : barcodes dict for the given barcode set
    #     barcode_well_ids = self.extract_well_ids(barcode_set, self.config['barcode_lookup_path'])
    #     stat_files = self.output_handler.get_stat_files()

    #     # TODO: This is the new way. Compare to the old above. Also check speed of execution
    #     start_time_new = time.time()
    #     stats = self._aggr_stats(stat_files, barcode_well_ids)
    #     # After executing the new method
    #     end_time_new = time.time()
    #     execution_time_new = end_time_new - start_time_new
    #     # print(f"STATS: New Method Execution Time: {execution_time_new} seconds")

    #     counts_loom_file = self.output_handler.get_counts_loom_file()

    #     # TODO: This is the new way. Compare to the old below. Also check speed of execution
    #     start_time_new = time.time()
    #     counts = self._process_loom_file(counts_loom_file['umicount_inex'])
    #     # After executing the new method
    #     end_time_new = time.time()
    #     execution_time_new = end_time_new - start_time_new

    #     stats = pd.concat([stats, counts], axis=1)

    #     # Save new stats to files
    #     self.save_data(stats.loc[:, ('Loom', ['UMI_genes_detected', 'UMI_read_counts'])], self.output_handler.stats_dir / f"{self.output_handler.sample_id}.umi_stats.txt")
    #     self.save_data(stats.loc[:, ('bc_set', 'WellID')], self.output_handler.stats_dir / f"{self.output_handler.sample_id}.well_barcodes.txt")

    #     # TODO: Remember to change the new_stats to stats once the new methods are confirmed to work correctly
    #     return stats


    def collect_stats(self):
        barcode_set = self.meta.get('barcode')
        if not barcode_set:
            logging.error("Missing barcode in metadata. Unable to extract well IDs.")
            return None

        barcode_lookup = self.config.get('barcode_lookup_path')
        if not barcode_lookup:
            logging.error("Missing barcode lookup path in config.")
            print(self.config)
            return None
        
        barcode_well_ids = self.extract_well_ids(barcode_set, barcode_lookup)
        if barcode_well_ids is None:
            logging.error("Well IDs extraction failed.")
            return None

        stat_files = self.output_handler.get_stat_files()
        stats = self._aggr_stats(stat_files, barcode_well_ids)
        if stats is None:
            logging.error("Aggregating stats failed.")
            return None

        counts_loom_file = self.output_handler.get_counts_loom_file()
        counts = self._aggr_umis_from_loom(counts_loom_file['umicount_inex'])
        if counts is None:
            logging.error("Aggregating UMI counts from loom failed.")
            return None

        if not stats.empty and not counts.empty: # and stats.index.equals(counts.index):
            stats = pd.concat([stats, counts], axis=1)
            if stats.empty:
                logging.error("Concatenated stats are empty.")
                return None
        else:
            logging.error("Stats and counts have incompatible indices or are empty.")
            print(stats.index, counts.index)
            return None

        # Save new stats to files
        self.save_data(stats.loc[:, ('Loom', ['UMI_genes_detected', 'UMI_read_counts'])], self.output_handler.stats_dir / f"{self.output_handler.sample_id}.umi_stats.txt")
        self.save_data(stats.loc[:, ('bc_set', 'WellID')], self.output_handler.stats_dir / f"{self.output_handler.sample_id}.well_barcodes.txt")

        return stats



    # def aggregate_data(self):
    #     """
    #     Main method to aggregate data from various sources.

    #     Returns:
    #         dict: A dictionary containing aggregated and processed data.
    #     """
    #     # Example of aggregating data
    #     stats_data = self.load_stats(self.output_handler.get_stats_file_path())
    #     umi_data = self.calc_umis(self.output_handler.get_umi_counts_file_path())

    #     # Combine data into a single structure
    #     aggregated_data = {
    #         "stats": stats_data,
    #         "umis": umi_data,
    #         # Add more data as needed
    #     }

    #     return aggregated_data


    ###########################################################################################################################
    ### NOTE: Below methods used for statistical data collection                                                              #
    ###########################################################################################################################

    def calc_umis(self, loom_file_path):
        # Implementation of UMI calculation logic
        # ...
        pass

    def load_stats(self, stats_file_path):
        # Implementation of stats loading logic
        # ...
        pass

    @staticmethod
    def extract_well_ids(barcode_set, barcode_lookup_fpath, reagent='1.5'):
        """
        Extracts well IDs corresponding to a given barcode set.

        Args:
            barcode_set (str): The barcode set to use for extracting well IDs (e.g., 1A).
            barcode_lookup_fpath (str): Path to the CSV file containing barcode and well ID mappings.
            reagent (str, optional): The reagent version used, defaults to '1.5'.

        Returns:
            pandas.Series: A Series where the index is barcodes and the values are corresponding well IDs.
            
        The function reads the barcode lookup CSV file and filters the data to get well IDs for the specified barcode set.
        If an unsupported reagent version is provided, it logs a warning and defaults to using '1.5'.
        """
        # Determine the target column based on reagent version
        if reagent == '1.5':
            target_col = 'XC'
        elif reagent == '1.0':
            target_col = 'XC_NovaSeq'
        else:
            logging.warning(f"Unsupported reagent version '{reagent}'. Using default '1.5'.")
            target_col = 'XC'

        try:
            # Read the CSV file
            bc_data = pd.read_csv(barcode_lookup_fpath, sep=',')
        except Exception as e:
            logging.error(f"Error reading barcode lookup file: {e}")
            return None

        # Filter data to get well IDs for the specified barcode set
        # Set the target column as index for efficient lookup
        bc_data.set_index(target_col, inplace=True)
        well_ids = bc_data.loc[bc_data.loc[:, 'BCset'] == barcode_set, 'WellID']

        return well_ids
    

    def _aggr_stats(self, stat_files, barcode_wells):
        """
        Aggregate statistical data from multiple files for a given set of barcodes.

        Args:
            stat_files (dict): Dictionary with paths to statistical files.
            barcode_wells (pd.Series): Series mapping well IDs to barcodes.

        Returns:
            pd.DataFrame: DataFrame with aggregated statistical data.
        """
        # Convert barcode_wells to DataFrame and set a MultiIndex
        data = pd.DataFrame(barcode_wells)

        # NOTE: The ', names=["source", "description"]' part is not necessary, but removing it will make the output
        # different to the old method's remnants. Discuss with the team as it might cause problems to users.
        data.columns = pd.MultiIndex.from_tuples([('bc_set', 'WellID')], names=["source", "description"])

        for file_type, file_path in stat_files.items():
            try:
                stats = pd.read_table(file_path)
            except EmptyDataError:
                logging.error(f"File is empty or unreadable: {file_path}")
                # Decide on further action - return None, skip, etc.
                return None
            except ValueError as e:
                logging.error(f"Error processing file {file_path}: {e}")
                # Decide on further action - return None, skip, etc.
                return None
            except Exception as e:
                logging.error(f"Unexpected error while reading file {file_path}: {e}")
                # Decide on further action - return None, skip, etc.
                return None

            if file_type == 'readspercell':
                # Filter out 'bad' rows and perform necessary transformations
                stats = stats[stats['RG'] != 'bad']
                stats = self._merge_data_by_type(stats, ['N', 'RG'])
                stats.set_index('RG', inplace=True)

                # NOTE: The ', names=["source", "description"]' part is not necessary, but removing it will make the output
                # different to the old method's remnants. Discuss with the team as it might cause problems to users.
                index = pd.MultiIndex.from_tuples([('readspercell', 'TotalReads')], names=["source", "description"])
                stats = pd.DataFrame(stats.sum(axis=1), columns=index)

            elif file_type == 'bc_umi_stats':
                # Process Barcode-UMI statistics and set MultiIndex
                stats.set_index('XC', inplace=True)

                # NOTE: The ', names=["source", "description"]' part is not necessary, but removing it will make the output
                # different to the old method's remnants. Discuss with the team as it might cause problems to users.
                stats.columns = pd.MultiIndex.from_tuples([('BC_UMI_stats', col) for col in stats.columns], names=["source", "description"])

            elif file_type == 'genecounts':
                # Process gene counts data and set MultiIndex
                stats = self._merge_data_by_type(stats, ['Count', 'SampleID'])
                stats.set_index('SampleID', inplace=True)

                # NOTE: The ', names=["source", "description"]' part is not necessary, but removing it will make the output
                # different to the old method's remnants. Discuss with the team as it might cause problems to users.
                stats.columns = pd.MultiIndex.from_tuples([('genecounts', col) for col in stats.columns], names=["source", "description"])

            else:
                continue

            try:
                # Merge data
                data = pd.merge(data, stats, how='left', left_index=True, right_index=True)
            except Exception as e:
                logging.error(f"Error occurred during merge operation: {e}")
                return None
        
        return data




    @staticmethod
    def _merge_data_by_type(input_data: pd.DataFrame, target_cols=['N', 'RG']) -> pd.DataFrame:
        """
        Prepares and merges data based on unique 'type' values and target columns.

        Args:
            input_data (pd.DataFrame): The input data to process.
            target_cols (list): Target columns for processing, default ['N', 'RG'].

        Returns:
            pd.DataFrame: The processed and merged data.
        """

        # NOTE: Data validation checks can be added here

        # Initial data setup as a DataFrame
        data = pd.DataFrame(input_data[target_cols[1]].unique(), columns=[target_cols[1]])

        # Process and merge data based on unique types
        for t in input_data['type'].unique():
            type_ext = input_data[input_data['type'] == t]
            type_ext = type_ext.rename(columns={target_cols[0]: t}).drop(columns=['type'])
            data = pd.merge(data, type_ext, on=[target_cols[1]], how='left')

        data.fillna(0, inplace=True)

        return data

    # TODO: Find better name
    def _aggr_umis_from_loom(self, loom_file_path):
        """
        Processes a single loom file to aggregate UMI & read counts.

        Args:
            loom_file_path (str): Path to the loom file.

        Returns:
            pd.DataFrame: DataFrame containing UMI read counts and UMI genes detected.
        """
        try:
            with lp.connect(loom_file_path, validate=False) as umi_loom:
                # if not hasattr(umi_loom.ca, 'cell_names') or len(umi_loom.ca.cell_names) == 0:
                #     logging.warning(f"Loom file missing expected data: {loom_file_path}")
                #     return pd.DataFrame()  # or return None
                
                # Get cell barcodes
                cell_barcodes = umi_loom.ca.cell_names

                # Initialize DataFrame to store results
                umi_data = pd.DataFrame(index=cell_barcodes)

                # Accumulate data for each cell
                for cell in cell_barcodes:
                    cell_idx = (cell_barcodes == cell).nonzero()[0]
                    umi_data.loc[cell, 'UMI_read_counts'] = umi_loom[:, cell_idx].sum()
                    umi_data.loc[cell, 'UMI_genes_detected'] = np.count_nonzero(np.asarray(umi_loom[:, cell_idx]))
        except Exception as e:
            logging.error(f"Error processing loom file {loom_file_path}: {e}")
            return None

        # NOTE: With only casting "UMI_genes_detected" to int the data is identical to the old method
        umi_data['UMI_genes_detected'] = umi_data['UMI_genes_detected'].astype(int)
        # NOTE: Casting both (UMI_read_counts and UMI_genes_detected) to int makes sense,
        # but the data is different from the old method. Discuss with the team as it might cause problems to users.
        # umi_data = umi_data.astype(int)

        # Create MultiIndex for columns
        umi_data.columns = pd.MultiIndex.from_product([['Loom'], umi_data.columns], names=["source", "description"])
        
        return umi_data


    ###########################################################################################################################
    ### NOTE: Below methods used for metadata collection                                                                      #
    ###########################################################################################################################

    def collect_meta(self, stats):
        version = self.get_zumis_version(self.output_handler.zumis_log_fpath)

        total_reads = self.meta.get('total_reads', None)
        total_reads = None
        if total_reads is None:
            total_reads = "Find in project summary report"
        else:
            total_reads = f"{int(total_reads / 1000000)} M"
        filtered_reads = int(stats.loc[:, ('readspercell', 'TotalReads')].sum(axis=0) / 1000000)  # Placeholder in MReads
        avg_readspercell = round(filtered_reads / 384 * 1000, 2)  # Placeholder in KReads

        metadata = {
            "zUMIs_version": version,
            # "sequencing_setup": self.meta['sequencing_setup'], #self.meta['sequencing_setup'], # In project_info
            # "barcode_set": self.meta['barcode_set'], # In sample->library_prep-> ... A/B/C ... -> barcode (or reagent_label) : as "SMARTSEQ3-22B"
            # "sample_id": self.sample.id, # Or is it id? Anyway in sample_info
            # "flowcells": None, # TODO: collect the 'sc_flowcells' from self.meta['library_prep'] ...[ A/B/C ] ... ['sequenced_fc'] and join them?
            # "genome": self.sample.project_info['ref_genome'], # In project_info -- if want short name: ref_gen.split(',')[0].split('(')[1].strip().lower()
            # "number of cells": 384, # TODO: Does this even make sense for Smart-seq3? It will always be 384.
            "total_reads": total_reads,
            "filtered_reads": f"{filtered_reads} M",  # Placeholder in MReads
            "avg_readspercell": f"{avg_readspercell} K"  # Placeholder in KReads
            # Add more metadata as needed
        }
        return metadata


    @staticmethod
    def get_zumis_version(zumis_log_fpath):
        """
        Retrieves the zUMIs version from the log file of a specific sample run.

        Args:
            zumis_log_fpath (str): Path to the zUMIs log file.

        Returns:
            str: The extracted zUMIs version number, or '--' if not found or an error occurs.
        """
        try:
            with open(zumis_log_fpath, 'r') as log_file:
                for line in reversed(log_file.readlines()):
                    if "zUMIs version" in line:
                        return line.split()[-1].strip()
        except FileNotFoundError:
            logging.error(f"zUMIs log file not found: {zumis_log_fpath}")
        except Exception as e:
            logging.error(f"Error reading zUMIs log file: {e}")

        return "--"







    ###########################################################################################################################
    ### NOTE: Below methods are helping utilities                                                                             #
    ###########################################################################################################################

    @staticmethod
    def save_data(data, path):
        data.to_csv(path, index=True, sep='\t')




    ###################################### DELETE BELOW #######################################################################

    # @staticmethod
    # def compare_dataframes(df1, df2):
    #     """
    #     Compare two dataframes and print differences.

    #     Args:
    #         df1 (pd.DataFrame): First dataframe.
    #         df2 (pd.DataFrame): Second dataframe.

    #     Returns:
    #         bool: True if dataframes are identical, False otherwise.
    #     """
    #     if df1.equals(df2):
    #         print("Dataframes are identical.")
    #         return True
    #     else:
    #         # If dataframes are not equal, find the differences
    #         diff = df1.compare(df2)
    #         print("Differences found:")
    #         print(diff)
    #         return False
