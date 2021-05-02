"""Utils for making final output columns generated by pythonify nicer
Col naming schema follows
<type>.<nlu_ref_identifier>.<field>
IF there is only 1 component of <type> in the pipe, the <type> will/can be ommitted.

- we remove all _<field> suffixex
- replace all '@' with '_'
"""

from sparknlp.annotator import *
from nlu.pipe.col_substitution import substitution_map_OS
from nlu.pipe.col_substitution import col_substitution_OS
import logging
logger = logging.getLogger('nlu')

""" NAMING SCHEMAS after pythonify procedure : 
### NAMING RESULT SCHEMA: 


results         = { configs.output_col_prefix+'_results'  : list(map(unpack_result,row))} if configs.get_result else {}
beginnings      = { configs.output_col_prefix+'_beginnings' : list(map(unpack_begin,row))} if configs.get_begin or configs.get_positions else {}
endings         = { configs.output_col_prefix+'_endings'    : next(map(unpack_end,row))} if configs.get_end or configs.get_positions else {}
embeddings      = { configs.output_col_prefix+'_embeddings' : next(map(unpack_embeddings,row))} if configs.get_embeds else {}


### METADATA NAMING SCHEMA

result = dict(zip(list(map(lambda x : 'meta_'+ configs.output_col_prefix + '_' + x, keys_in_metadata)),meta_values_list))




"""
from nlu.pipe.pipe_logic import PipeUtils
class ColSubstitutionUtils():
    """Utils for substituting col names in Pythonify to short and meaningful names.
    Uses custom rename methods for either PySpark or Pandas
    """
    from sparknlp.annotator import MarianTransformer
    cleanable_splits = ['ner_converter','spell','ner_to_chunk_converter','train','classify','ner','med_ner','dl','match','clean','sentiment','embed','embed_sentence','embed_chunk','explain','pos','resolve_chunk','resolve',]
    all_langs        = ['en','et','bh','am','da','fr','de','it','nb','no','nn','pl','pt','ru','es','af','ar','hy','eu','bn','br','bg','ca','cs','eo','fi','gl','el','ha','he','hi','hu','id','ga','ja','la','lv','mr','fa','ro','sk','sl','so','st','sw','sv','th','tr','uk','yo','zu','zh','xx','ur','ko']
    @staticmethod
    def substitute_col_names(df,anno_2_ex,pipe,drop_debug_cols=True):
        """
        Some truly irrelevant cols might be dropped, regardless of anno Extractor config
        Some truly irrelevant cols might be dropped, regardless of anno Extractor config
        0. Get list of annotator classes that are duplicates. Check inside the NLU Component Embelishment
        1. Get list of cols derived by component
        2. Substitute list of cols in DF with custom logic
        """
        substitution_fn = 'TODO'
        new_cols = {}
        if pipe.has_licensed_components :
            from nlu.pipe.col_substitution import col_substitution_HC
            from nlu.pipe.col_substitution import substitution_map_HC
        deducted_component_names = ColSubstitutionUtils.deduct_component_names(pipe)
        for c in pipe.components :
            cols_to_substitute = ColSubstitutionUtils.get_final_output_cols_of_component(c,df,anno_2_ex)

            if type(c.model) in substitution_map_OS.OS_anno2substitution_fn.keys():
                substitution_fn = substitution_map_OS.OS_anno2substitution_fn[type(c.model)]['default']
            if pipe.has_licensed_components and substitution_fn != 'TODO':
                if type(c.model) in substitution_map_HC.HC_anno2substitution_fn.keys():
                    substitution_fn = substitution_map_HC.HC_anno2substitution_fn[type(c.model)]['default']
            if substitution_fn =='TODO':
                logger.info(f"Could not find substitution function for c={c}, leaving col names untouched")
                new_cols.update(dict(zip(cols_to_substitute,cols_to_substitute)))
                continue
            # dic, key=old_col, value=new_col. Some cols may be omitted and missing from the dic which are deemed irrelevant. Behaivour can be disabled by setting drop_debug_cols=False
            new_cols = {**new_cols, **(substitution_fn(c,cols_to_substitute,deducted_component_names[c]))}

        cols_to_rename = list(new_cols.keys() )
        for k in cols_to_rename:
            # some cols might not exist because no annotations generated, so we need to double check it really exists
            if k not in df.columns: del new_cols[k]
        return df.rename(columns = new_cols)[new_cols.values()] if drop_debug_cols else df.rename(columns = new_cols)


    @staticmethod
    def get_final_output_cols_of_component(c,df,anno_2_ex):
        # get_final_output_cols_of_component(self.components[1], pretty_df, anno_2_ex_config)
        """Get's a list of all columns that have been derived in the pythonify procedure from the component c in dataframe df for anno_2_ex configs """
        og_output_col = c.info.spark_output_column_names[0]
        configs       = anno_2_ex[og_output_col]
        result_cols   = []
        if configs.get_annotator_type                 : result_cols.append(configs.output_col_prefix+'_types')
        if configs.get_result                         : result_cols.append(configs.output_col_prefix+'_results')
        if configs.get_begin or configs.get_positions : result_cols.append(configs.output_col_prefix+'_beginnings')
        if configs.get_end   or configs.get_positions : result_cols.append(configs.output_col_prefix+'_endings')
        if configs.get_embeds                         : result_cols.append(configs.output_col_prefix+'_embeddings')
        # find all metadata fields generated by compoent
        for col in df.columns :
            if 'meta_'+ configs.output_col_prefix in col:
                base_meta_prefix = 'meta_'+ configs.output_col_prefix
                meta_col_name = base_meta_prefix + col.split(base_meta_prefix)[-1]
                if meta_col_name in df.columns :
                    # special case for overlapping names with _
                    if col.split(base_meta_prefix)[-1].split('_')[1].isnumeric() and not c.info.outputs[0].split('_')[-1].isnumeric(): continue
                    if col.split(base_meta_prefix)[-1].split('_')[1].isnumeric() and c.info.outputs[0].split('_')[-1].isnumeric():
                        id1 = int(col.split(base_meta_prefix)[-1].split('_')[1])
                        id2 = int(c.info.outputs[0].split('_')[-1])
                        if id1 != id2 : continue
                    result_cols.append(meta_col_name)
                else : logger.info(f"Could not find meta col for c={c}, col={col}. Ommiting col..")
        return result_cols


    @staticmethod
    def deduct_component_names(pipe):
        """Deduct a meaningful name for Embeddings, classifiers, resolvesr, relation extractors, etc..
        Will return a dict that maps every Annotator Class to a String Name. If String_Name =='' that means, it can be omtited for naming and the unique_default name schema should be used,
        since that annotator is unique in the pipe
        """
        import nlu.pipe.col_substitution.name_deduction.name_deductable_annotators_OS as deductable_OS
        max_depth = 10
        result_names = {}
        for c in pipe.components :
            result_names[c]='UNIQUE' # assuemd uniqe, if not updated in followign steps
            is_always_name_deductable_component = False
            hc_deducted = False
            if pipe.has_licensed_components :
                import nlu.pipe.col_substitution.name_deduction.name_deductable_annotators_HC as deductable_HC
                if type(c.model) not in deductable_HC.name_deductable_HC and type(c.model) not in deductable_OS.name_deductable_OS: continue
                else : hc_deducted = True
                if type(c.model) in deductable_HC.always_name_deductable_HC: is_always_name_deductable_component=True

            if type(c.model) not in deductable_OS.name_deductable_OS and not hc_deducted : continue
            if type(c.model) in deductable_OS.always_name_deductable_OS: is_always_name_deductable_component=True

            same_components = []
            for other_c in pipe.components :
                if c is other_c: continue
                if c.info.type == other_c.info.type: same_components.append(other_c)
            if len(same_components) or is_always_name_deductable_component:
                # make sure each name is unique among the components of same type
                cur_depth = 1
                other_names = [ColSubstitutionUtils.deduct_name_from_nlu_ref_at_depth(other_c) for other_c in same_components]
                c_name = ColSubstitutionUtils.deduct_name_from_nlu_ref_at_depth(c)
                while c_name in other_names and cur_depth < max_depth:
                    cur_depth += 1
                    other_names = [ColSubstitutionUtils.deduct_name_from_nlu_ref_at_depth(other_c) for other_c in same_components]
                    c_name = ColSubstitutionUtils.deduct_name_from_nlu_ref_at_depth(c,cur_depth)
                result_names[c]=c_name
            else :
                result_names[c]='UNIQUE' # no name insertion required
        return result_names

    @staticmethod
    def deduct_name_from_nlu_ref_at_depth(c, depth=1):
        if isinstance(c.model, MarianTransformer): return c.info.nlu_ref.split('xx.')[-1].replace('marian.','')
        splits = c.info.nlu_ref.split('.')
        #remove all name irrelevant splits
        while  len(splits) >1 and (splits[0] in ColSubstitutionUtils.all_langs or splits[0] in ColSubstitutionUtils.cleanable_splits): splits.pop(0)
        if len(splits)==0:
            if isinstance(c.model,(NerDLModel,NerConverter)): return 'ner'
            return c.info.nlu_ref.replace("@","_")
        else : return '_'.join(splits[:depth])

