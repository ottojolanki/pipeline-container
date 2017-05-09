#!/usr/bin/env python
# filter_qc 0.0.1
# Generated by dx-app-wizard.
#
# Basic execution pattern: Your app will run on a single machine from
# beginning to end.
#
# See https://wiki.dnanexus.com/Developer-Portal for documentation and
# tutorials on how to modify this file.
#
# DNAnexus Python Bindings (dxpy) documentation:
#   http://autodoc.dnanexus.com/bindings/python/current/

import os
import sys
import subprocess
import shlex
import common
import logging
from pprint import pprint

logger = logging.getLogger(__name__)
logger.propagate = False
logger.setLevel(logging.INFO)


def dup_parse(fname):
    with open(fname, 'r') as dup_file:
        if not dup_file:
            return None
        lines = iter(dup_file.read().splitlines())
        for line in lines:
            if line.startswith('## METRICS CLASS'):
                headers = lines.next().rstrip('\n').lower()
                metrics = lines.next().rstrip('\n')
                break
        headers = headers.split('\t')
        metrics = metrics.split('\t')
        headers.pop(0)
        metrics.pop(0)

        dup_qc = dict(zip(headers, metrics))

    return dup_qc


def pbc_parse(fname):

    with open(fname, 'r') as pbc_file:
        if not pbc_file:
            return None

        lines = pbc_file.read().splitlines()
        line = lines[0].rstrip('\n')
        # PBC File output:
        #   TotalReadPairs <tab>
        #   DistinctReadPairs <tab>
        #   OneReadPair <tab>
        #   TwoReadPairs <tab>
        #   NRF=Distinct/Total <tab>
        #   PBC1=OnePair/Distinct <tab>
        #   PBC2=OnePair/TwoPair

        headers = ['TotalReadPairs',
                   'DistinctReadPairs',
                   'OneReadPair',
                   'TwoReadPairs',
                   'NRF',
                   'PBC1',
                   'PBC2']
        metrics = line.split('\t')

        pbc_qc = dict(zip(headers, metrics))

    return pbc_qc


def main(input_bam, paired_end, samtools_params, debug):

    # create a file handler
    handler = logging.FileHandler('filter_qc.log')

    if debug:
        handler.setLevel(logging.DEBUG)
    else:
        handler.setLevel(logging.INFO)
    logger.addHandler(handler)
    # input_json is no longer used
    # # if there is input_JSON, it over-rides any explicit parameters
    # if input_JSON:
    #     if 'input_bam' in input_JSON:
    #         input_bam = input_JSON['input_bam']
    #     if 'paired_end' in input_JSON:
    #         paired_end = input_JSON['paired_end']
    #     if 'samtools_params' in input_JSON:
    #         samtools_params = input_JSON['samtools_params']

    # this is now handled by the platform input validator
    # if not input_bam:
    #     logger.error('input_bam is required')
    #     raise Exception
    # assert paired_end is not None, 'paired_end is required, explicitly or in input_JSON'

    raw_bam_basename = (input_bam.rstrip('.bam')).split('/')[-1]

    subprocess.check_output('set -x; ls -l', shell=True)

    filt_bam_prefix = raw_bam_basename + ".filt.srt"
    filt_bam_filename = filt_bam_prefix + ".bam"
    if paired_end:
        # =============================
        # Remove  unmapped, mate unmapped
        # not primary alignment, reads failing platform
        # Remove low MAPQ reads
        # Only keep properly paired reads
        # Obtain name sorted BAM file
        # ==================
        tmp_filt_bam_prefix = "tmp.%s" % (filt_bam_prefix)  # was tmp.prefix.nmsrt
        tmp_filt_bam_filename = tmp_filt_bam_prefix + ".bam"
        out, err = common.run_pipe([
            # filter: -F 1804 FlAG bits to exclude; -f 2 FLAG bits to reqire;
            # -q 30 exclude MAPQ < 30; -u uncompressed output
            # exclude FLAG 1804: unmapped, next segment unmapped, secondary
            # alignments, not passing platform q, PCR or optical duplicates
            # require FLAG 2: properly aligned
            "samtools view -F 1804 -f 2 %s -u %s" % (samtools_params, raw_bam_basename),
            # sort:  -n sort by name; - take input from stdin;
            # out to specified filename
            # Will produce name sorted BAM
            "samtools sort -n - %s" % (tmp_filt_bam_prefix)])
        if err:
            logger.error("samtools error: %s" % (err))
        # Remove orphan reads (pair was removed)
        # and read pairs mapping to different chromosomes
        # Obtain position sorted BAM
        subprocess.check_output('set -x; ls -l', shell=True)
        out, err = common.run_pipe([
            # fill in mate coordinates, ISIZE and mate-related flags
            # fixmate requires name-sorted alignment; -r removes secondary and
            # unmapped (redundant here because already done above?)
            # - send output to stdout
            "samtools fixmate -r %s -" % (tmp_filt_bam_filename),
            # repeat filtering after mate repair
            "samtools view -F 1804 -f 2 -u -",
            # produce the coordinate-sorted BAM
            "samtools sort - %s" % (filt_bam_prefix)])
        subprocess.check_output('set -x; ls -l', shell=True)
    else:  # single-end data
        # =============================
        # Remove unmapped, mate unmapped
        # not primary alignment, reads failing platform
        # Remove low MAPQ reads
        # Obtain name sorted BAM file
        # ==================
        with open(filt_bam_filename, 'w') as fh:
            samtools_filter_command = (
                "samtools view -F 1804 %s -b %s"
                % (samtools_params, input_bam)
                )
            logger.info(samtools_filter_command)
            subprocess.check_call(
                shlex.split(samtools_filter_command),
                stdout=fh)

    # ========================
    # Mark duplicates
    # ======================
    tmp_filt_bam_filename = raw_bam_basename + ".dupmark.bam"
    dup_file_qc_filename = raw_bam_basename + ".dup.qc"
    picard_string = ' '.join([
        "java -Xmx4G -jar /picard/MarkDuplicates.jar",
        "INPUT=%s" % (filt_bam_filename),
        "OUTPUT=%s" % (tmp_filt_bam_filename),
        "METRICS_FILE=%s" % (dup_file_qc_filename),
        "VALIDATION_STRINGENCY=LENIENT",
        "ASSUME_SORTED=true",
        "REMOVE_DUPLICATES=false"
        ])
    logger.info(picard_string)
    subprocess.check_output(shlex.split(picard_string))
    os.rename(tmp_filt_bam_filename, filt_bam_filename)

    if paired_end:
        final_bam_prefix = raw_bam_basename + ".filt.srt.nodup"
    else:
        final_bam_prefix = raw_bam_basename + ".filt.nodup.srt"
    final_bam_filename = final_bam_prefix + ".bam"  # To be stored
    final_bam_index_filename = final_bam_filename + ".bai"  # To be stored
    # QC file
    final_bam_file_mapstats_filename = final_bam_prefix + ".flagstat.qc"

    if paired_end:
        samtools_dedupe_command = \
            "samtools view -F 1804 -f2 -b %s" % (filt_bam_filename)
    else:
        samtools_dedupe_command = \
            "samtools view -F 1804 -b %s" % (filt_bam_filename)

    # ============================
    # Remove duplicates
    # Index final position sorted BAM
    # ============================
    with open(final_bam_filename, 'w') as fh:
        logger.info(samtools_dedupe_command)
        subprocess.check_call(
            shlex.split(samtools_dedupe_command),
            stdout=fh)

    # Index final bam file
    samtools_index_command = \
        "samtools index %s %s" % (final_bam_filename, final_bam_index_filename)
    logger.info(samtools_index_command)
    subprocess.check_output(shlex.split(samtools_index_command))

    # Generate mapping statistics
    with open(final_bam_file_mapstats_filename, 'w') as fh:
        flagstat_command = "samtools flagstat %s" % (final_bam_filename)
        logger.info(flagstat_command)
        subprocess.check_call(shlex.split(flagstat_command), stdout=fh)

    # =============================
    # Compute library complexity
    # =============================
    # Sort by name
    # convert to bedPE and obtain fragment coordinates
    # sort by position and strand
    # Obtain unique count statistics
    pbc_file_qc_filename = final_bam_prefix + ".pbc.qc"

    # PBC File output
    # TotalReadPairs [tab]
    # DistinctReadPairs [tab]
    # OneReadPair [tab]
    # TwoReadPairs [tab]
    # NRF=Distinct/Total [tab]
    # PBC1=OnePair/Distinct [tab]
    # PBC2=OnePair/TwoPair
    if paired_end:
        steps = [
            "samtools sort -no %s -" % (filt_bam_filename),
            "bamToBed -bedpe -i stdin",
            r"""awk 'BEGIN{OFS="\t"}{print $1,$2,$4,$6,$9,$10}'"""]
    else:
        steps = [
            "bamToBed -i %s" % (filt_bam_filename),
            r"""awk 'BEGIN{OFS="\t"}{print $1,$2,$3,$6}'"""]
    steps.extend([
        # TODO this should be implemented as an explicit list of allowable
        # names, so that mapping can be done to a complete reference
        "grep -v 'chrM'",
        "sort",
        "uniq -c",
        r"""awk 'BEGIN{mt=0;m0=0;m1=0;m2=0} ($1==1){m1=m1+1} ($1==2){m2=m2+1} {m0=m0+1} {mt=mt+$1} END{printf "%d\t%d\t%d\t%d\t%f\t%f\t%f\n",mt,m0,m1,m2,m0/mt,m1/m0,m1/m2}'"""
        ])
    out, err = common.run_pipe(steps, pbc_file_qc_filename)
    if err:
        logger.error("PBC file error: %s" % (err))

    logger.info("Uploading results files to the project")

    print (final_bam_filename)
    print (final_bam_index_filename)
    print (dup_file_qc_filename)
    print (pbc_file_qc_filename)
    #filtered_bam = dxpy.upload_local_file(final_bam_filename)
    #filtered_bam_index = dxpy.upload_local_file(final_bam_index_filename)
    #filtered_mapstats = \
    #    dxpy.upload_local_file(final_bam_file_mapstats_filename)
    #dup_file = dxpy.upload_local_file(dup_file_qc_filename)
    #pbc_file = dxpy.upload_local_file(pbc_file_qc_filename)
    
    dup_qc = dup_parse(dup_file_qc_filename)
    pbc_qc = pbc_parse(pbc_file_qc_filename)
    logger.info("dup_qc: %s" % (dup_qc))
    logger.info("pbc_qc: %s" % (pbc_qc))

    # Return links to the output files
    output = {
        #"filtered_bam": dxpy.dxlink(filtered_bam),
        #"filtered_bam_index": dxpy.dxlink(filtered_bam_index),
        #"filtered_mapstats": dxpy.dxlink(filtered_mapstats),
        #"dup_file_qc": dxpy.dxlink(dup_file),
        #"pbc_file_qc": dxpy.dxlink(pbc_file),
        "paired_end": paired_end,
        "NRF": pbc_qc.get('NRF'),
        "PBC1": pbc_qc.get('PBC1'),
        "PBC2": pbc_qc.get('PBC2'),
        "duplicate_fraction": dup_qc.get('percent_duplication')
    }
    logger.info("Exiting with output:\n%s" % (pprint(output)))
    return output

sys.path.append(os.path.abspath(sys.argv[2]))
main(sys.argv[1], False, '', False)
