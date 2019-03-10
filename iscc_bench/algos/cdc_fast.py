# -*- coding: utf-8 -*-
import logging
from io import BytesIO
from os.path import basename
from statistics import mean

from iscc_bench.algos.metrics import containment
from iscc_bench.algos.slide import sliding_window
from iscc_bench.readers.gutenberg import gutenberg

logr = logging.getLogger(__name__)

MAX_INT64 = 2**64-1

GEAR2_NORM = 512
GEAR2_MIN = 128
GEAR2_MAX = 4096
GEAR2_MASK1 = 0b1101100110110100000000
GEAR2_MASK2 = 0b11100101010110000000

CHUNKING_GEAR = [
    9584138480181866666, 4739450037122062430, 1042006760432515769, 10675154520554330663, 15869016765101259526,
    8970928072383595559, 1399451202205921674, 14523822808097149755, 16268498464839721299, 10481172452375523505,
    17104617054662428007, 1589812074021361642, 5529368114994898429, 16097147859444922117, 7366391750793198740,
    11100538009918328137, 1389689728615383157, 4977138822009172500, 908349889557194910, 14452518814433479233,
    2122926032271239532, 591612022955043504, 9379034436570273189, 12748258297147873806, 4307386326245858243,
    13845229916084989633, 11224472648935237303, 7047696390035316099, 2021133566789993437, 17387162748083618158,
    11746787256992261957, 6644482612611712714, 15729398955930993486, 18187694890389888249, 13375007170405426180,
    4646676434852504131, 13152698236329639071, 899989819383117385, 1604228284900755822, 13429168974601667864,
    3706248770764044735, 3719799868214789934, 339511817415309475, 12306710798301877171, 9844020938499650522,
    13507342816267977422, 15331217600725578556, 7506003564454403634, 17943236144189306428, 282153689319390566,
    7654271695669749695, 2650412143911437370, 6193440044944269691, 9296646612477743744, 15077579129862372948,
    67630558006200567, 11937031764123301943, 1634327986517329169, 16073934395340319514, 11660580892053471307,
    12301495579660351243, 16908718276972184511, 6851717516129410187, 13288278789994352315, 17482170774163197685,
    12177168157992128323, 1679876621412537528, 15666827561093998679, 4235032027386979601, 17396011814487376094,
    2036017399572567727, 4977152437582070133, 11341111713611820820, 5866443846249079891, 5131277185090952872,
    8325299058005558320, 5701450024662049407, 15870252139465586153, 641910037851244477, 5172232175829573378,
    2261684586607900474, 11396825283718526131, 12408680075109652465, 7761877592432080901, 13820035802684848169,
    8150091535052795450, 1103357817677537274, 13470426615970288837, 4696524065622673976, 9336804607285957500,
    13043178028673218162, 7139020806469476608, 12450708403507569100, 2877039905016676547, 15118872351294838361,
    3277072151995360446, 1979210712452295885, 14822651643543876641, 5849754172112174627, 13664543478254756807,
    16186972696580520130, 14259131679517995788, 1772106294408535188, 2668205339646827112, 3734021086026184498,
    4257506854909152229, 6797729639474582495, 3708095106171770747, 15445894064208319783, 11045733249000282278,
    6925260395759991481, 6761677416581440942, 3134957115005596133, 5496794829211694837, 225035875953155227,
    18051382753002575119, 6911658830635795092, 6648838042848840266, 7680838377178993211, 14373546918520540763,
    7385952462173201391, 7500965322394952100, 15539214383494689771, 14355530880918970074, 4040759991734970063,
    1335151750647325670, 13713452291232361388, 8852782707920062625, 6076783566257059794, 14451547968886132839,
    6756882940270420653, 17423128808598833972, 5877907771709558759, 14308413074787508328, 12294727846616188882,
    13766545313722789196, 7000331838802888702, 15110028412924060381, 15869145452552081798, 10836437530623796047,
    1273143868608979117, 17728019699248776702, 379008101491021165, 6658832383485441856, 6005905363267598720,
    4792802520786808134, 17024928019214694263, 7949301678895773307, 14602122883430422290, 6416689239839102410,
    18112987618441438141, 5424513836620859057, 12327961344656070412, 18229731317766561349, 6214341855555485197,
    14659604854593022088, 18341976098904231516, 9093141550798891276, 4487469223051523007, 12576621890114680116,
    11368566035561888278, 16632902625329423294, 13764076000271015053, 11494903226088746337, 14079100963083335535,
    5976601008655555884, 5685807667042201553, 16503266544486236927, 5505089898459277917, 17076606531971661551,
    939769563919939433, 17217248958964594832, 11196454443995107214, 13253314556391295544, 17340262486782904124,
    5483165811177129540, 121736889831618943, 6318157315988658220, 14520375112718267902, 689388276875596813,
    5273319774965020902, 7975410517565653865, 13935269057627157047, 16821796908479891795, 5882048506860913277,
    18003709489856105216, 1424933842252756366, 6634557257081066175, 16179356916240399588, 11153419399622634817,
    15654294493035402949, 2652919763627807814, 16437183290373292867, 16903315446495122175, 3575318971059548300,
    3073697257555445515, 16187136733800880291, 15191964085364171996, 11982016174040399757, 1948589207658719032,
    14444449012119241408, 7130754012353479650, 7480280819583944745, 3603028513293740433, 7021162527209392860,
    2124450348946366496, 14349140477237426219, 7396225914272122063, 16288120608246645021, 7309794834881975478,
    16746864570463829614, 9239996606832866982, 14126189643057989505, 5785181374404079776, 16681042508550037223,
    9085478584447523753, 12879577862603639783, 13351556131001260565, 10860701565908202403, 9109516948909639475,
    2942389181877553466, 1907923359833671766, 1700327967934711796, 4355952370607563279, 6159416062364401684,
    8120694842642123744, 4670360822544180192, 12684384265447906291, 11518186189217338692, 14839496566538901930,
    13515715604989800698, 12135065096961528408, 9056982071865174221, 12690699907549395246, 2080896935929507230,
    14546126411900211421, 6222235617711806766, 13387691023848518640, 1259523422199249803, 1733690531272524911,
    16691543548458831721, 3252085970219428027, 790320086519395195, 8366099548552136926, 357423734596052102,
    6375583027298966643, 88639135753272123, 13813972796887520980, 8203570281250814300, 18377325011640278855,
    2922465295015278442, 2164203008979443347, 7447171935848155518, 3663261456454345351, 5865411828910435346,
    13570376904595974307
]


def data_chunks(data):

    if isinstance(data, str):
        data = open(data, 'rb')

    if not hasattr(data, 'read'):
        data = BytesIO(data)

    section = data.read(GEAR2_MAX)
    while True:
        if len(section) < GEAR2_MAX:
            section += data.read(GEAR2_MAX)
        if len(section) == 0:
            break
        boundary = chunk_length(
            section,
            GEAR2_NORM,
            GEAR2_MIN,
            GEAR2_MAX,
            GEAR2_MASK1,
            GEAR2_MASK2,
        )

        yield section[:boundary]
        section = section[boundary:]


def chunk_length(data, norm_size, min_size, max_size, mask_1, mask_2):

    data_length = len(data)
    i = min_size
    pattern = 0

    if data_length <= min_size:
        return data_length

    barrier = min(norm_size, data_length)
    while i < barrier:
        pattern = ((pattern << 1) + CHUNKING_GEAR[data[i]]) & MAX_INT64
        if not pattern & mask_1:
            return i
        i = i + 1

    barrier = min(max_size, data_length)
    while i < barrier:
        pattern = ((pattern << 1) + CHUNKING_GEAR[data[i]]) & MAX_INT64
        if not pattern & mask_2:
            return i
        i = i + 1
    return i


SAMPLES = 500


def test_data_chunks():
    fps = list(gutenberg())[:SAMPLES]

    losses = []
    chunk_sizes = []
    num_chunks = []
    similarities = []
    dissimilarities = []

    for fp_a, fp_b, fp_c in sliding_window(fps, size=3, step=2, fillvalue=None):
        if fp_b is None:
            break
        if fp_c is None:
            fp_c = fps[0]

        chunks_a = list(data_chunks(fp_a))
        chunks_b = list(data_chunks(fp_b))
        chunks_c = list(data_chunks(fp_c))

        chunk_sizes.extend(len(c) for c in chunks_a)

        def cut_regions(chunks):
            regs = []
            for a, b in sliding_window(chunks, size=2, step=1):
                regs.append(a[-6:] + b[:6])
            return regs

        # select cutpoint regions only
        chunks_a = cut_regions(chunks_a)
        chunks_b = cut_regions(chunks_b)
        chunks_c = cut_regions(chunks_c)

        num_chunks.append(len(chunks_a))

        sim_sim = containment(chunks_a, chunks_b)
        similarities.append(sim_sim)

        sim_dif = containment(chunks_a, chunks_c)
        dissimilarities.append(sim_dif)
        loss = sim_sim / (sim_dif or 0.00001)
        logr.debug(f'Loss: {loss:.3f} Sim: {sim_sim:.3f} Dif: {sim_dif:.3f} ({basename(fp_a)})')
        losses.append(loss)
    return {
        'status': 'ok',
        'loss': mean(losses),
        'avg_num_chunks': mean(num_chunks),
        'avg_chunk_size': mean(chunk_sizes),
        'max_chunk_size': max(chunk_sizes),
        'avg_sim': mean(similarities),
        'avg_dis': mean(dissimilarities),
    }


if __name__ == '__main__':
    from pprint import pprint
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=log_format)
    pprint(test_data_chunks())
