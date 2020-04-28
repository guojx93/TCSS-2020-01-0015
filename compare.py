import random
import copy
import math
import time

def readGraph(path, p):
    neighbor = {}
    edges = {}
    nodes = set()
    f = open(path, 'r')
    for line in f.readlines():
        line = line.strip()
        if not len(line) or line.startswith('#'):
            continue
        row = line.split()
        src = int(row[0])
        dst = int(row[1])
        nodes.add(src)
        nodes.add(dst)
        if neighbor.get(src) is None:
            neighbor[src] = set()
        if neighbor.get(dst) is None:
            neighbor[dst] = set()
        edges[(min(src,dst), max(src,dst))] = p
        neighbor[src].add(dst)
        neighbor[dst].add(src)
    return Graph(nodes, edges, neighbor)

class Graph:
    nodes = None
    nodes_acceptance = {}
    edges = None
    neighbor = None
    node_num = None
    edge_num = None
    def __init__(self, nodes, edges, neighbor):
        self.nodes = nodes
        self.edges = edges
        self.neighbor = neighbor
        self.node_num = len(nodes)
        self.edge_num = len(edges)
        for node in self.nodes:
            self.nodes_acceptance[node] = random.random()
    def get_neighbor(self, node):
        itsNeighbor = self.neighbor.get(node)
        if itsNeighbor is None:
            return set()
        return self.neighbor[node]

def isHappened(prob):
    if prob == 1:
        return True
    if prob == 0:
        return False
    rand = random.random()
    if rand <= prob:
        return True
    else:
        return False

def adaptiveInvitation(graph, R, b, k):
    time_start = time.time()
    H = set()
    edge_realization = {}
    for edge in graph.edges:
        edge_realization[edge] = '?'
    user_participant = {}
    for v in graph.nodes:
        user_participant[v] = k + 1

    user_gain = {}
    for v in graph.nodes:
        user_gain[v] = simulate(graph, R, k, edge_realization, user_participant, v)
    u1 = findMax(user_gain)
    H.add(u1)
    rand = random.random()
    if rand < graph.nodes_acceptance[u1]:
        user_participant[u1] = 0
        update(graph, edge_realization, user_participant, k, u1)
        del user_gain[u1]
        for v in (graph.nodes - H):
            if check(graph, 2 * k, u1, v):
                user_gain[v] = simulate(graph, R, k, edge_realization, user_participant, v)
    else:
        del user_gain[u1]

    step = b / 6

    stat = {}
    ttime = {}
    for i in range(2, b + 1):
        ui = findMax(user_gain)
        H.add(ui)
        rand = random.random()
        if rand < graph.nodes_acceptance[ui]:
            user_participant[ui] = 0
            update(graph, edge_realization, user_participant, k, ui)
            del user_gain[ui]
            for v in (graph.nodes - H):
                if check(graph, 2 * k, ui, v):
                    user_gain[v] = simulate(graph, R, k, edge_realization, user_participant, v)
        else:
            del user_gain[ui]
        if i % step == 0:
            profit = findProfit(user_participant, R)
            stat[i] = profit
            ttime[i] = time.time() - time_start
    return stat, ttime

def findProfit(user_participant, R):
    profit = 0
    for user in user_participant:
        profit += R[user_participant[user]]
    return profit

def check(graph, dist, u, v):
    visited = set()
    curLevel = set()
    visited.add(u)
    curLevel.add(u)
    i = 0
    while len(curLevel) != 0 and i < dist:
        next = set()
        i += 1
        for node in curLevel:
            for neig in graph.get_neighbor(node):
                if neig not in visited:
                    next.add(neig)
                    visited.add(neig)
        curLevel = next
    if v in visited:
        return True
    return False

def update(graph, edge_realization, user_participant, k, u):
    curLevel = set()
    curLevel.add(u)
    i = 0
    while len(curLevel) != 0 and i < k:
        next = set()
        i += 1
        for node in curLevel:
            for neig in graph.get_neighbor(node):
                edge = (min(node, neig), max(node, neig))
                if edge_realization[edge] == 1:
                    if i < user_participant[neig]:
                        user_participant[neig] = i
                        next.add(neig)
                elif edge_realization[edge] == '?':
                    rand = random.random()
                    if rand < graph.edges[edge]:
                        edge_realization[edge] = 1
                        if i < user_participant[neig]:
                            user_participant[neig] = i
                            next.add(neig)
                    else:
                        edge_realization[edge] = 0
        curLevel = next
    return None

def findMax(user_gain):
    ui = 0
    max_gain = 0
    for node in user_gain:
        if user_gain[node] > max_gain:
            ui = node
            max_gain = user_gain[node]
    return ui

def compute(graph, R, k, edge_realization, user_participant, u):
    L = []
    S = set()
    S.add(u)
    L.append([[u, 0]])
    Delta = 0
    for i in range(1, k + 1):
        Vi = []
        for v in L[i - 1]:
            for vPrime in graph.get_neighbor(v[0]):
                if vPrime not in S:
                    Vi.append([vPrime, 0])
                    S.add(vPrime)
        L.append(Vi)
    L[0][0][1] = graph.nodes_acceptance[u]
    Delta += graph.nodes_acceptance[u] * (R[0] - R[user_participant[u]])
    for i in range(1, k + 1):
        m = 0
        for v in L[i]:
            n = 0
            t = 1
            for vPrime in L[i - 1]:
                edge = (min(v[0],vPrime[0]),max(v[0],vPrime[0]))
                if edge in graph.edges:
                    if edge_realization[edge] == 1:
                        t *= (1 - L[i - 1][n][1])
                    elif edge_realization[edge] == '?':
                        t *= (1 - graph.edges[edge] * L[i - 1][n][1])
                n += 1
            L[i][m][1] = 1 - t
            m += 1
        m = 0
        for v in L[i]:
            if i < user_participant[v[0]]:
                Delta += L[i][m][1] * (R[i] - R[user_participant[v[0]]])
            m += 1
    return Delta

def simulate(graph, R, k, edge_realization, user_participant, u, N=10):
    Delta = 0
    for n in range(N):
        user_participant_copy = copy.deepcopy(user_participant)
        Delta += R[0] - R[user_participant_copy[u]]
        user_participant_copy[u] = 0
        edge_realization_copy = copy.deepcopy(edge_realization)
        curLevel = set()
        curLevel.add(u)
        i = 0
        while len(curLevel) != 0 and i < k:
            next = set()
            i += 1
            for node in curLevel:
                for neig in graph.get_neighbor(node):
                    edge = (min(node, neig), max(node, neig))
                    if edge_realization_copy[edge] == 1:
                        if i < user_participant_copy[neig]:
                            Delta += R[i] - R[user_participant_copy[neig]]
                            user_participant_copy[neig] = i
                            next.add(neig)
                    elif edge_realization_copy[edge] == '?':
                        rand = random.random()
                        if rand < graph.edges[edge]:
                            edge_realization_copy[edge] = 1
                            if i < user_participant_copy[neig]:
                                Delta += R[i] - R[user_participant_copy[neig]]
                                user_participant_copy[neig] = i
                                next.add(neig)
                        else:
                            edge_realization_copy[edge] = 0
            curLevel = next
    return (Delta / N) * graph.nodes_acceptance[u]

def randomm(graph, R, b, k):
    H = set()
    edge_realization = {}
    for edge in graph.edges:
        edge_realization[edge] = '?'
    user_participant = {}
    for v in graph.nodes:
        user_participant[v] = k + 1

    step = b / 6
    stat = {}
    candidate = list(graph.nodes)
    for i in range(1, b + 1):
        rand = random.randint(0, len(candidate) - 1)
        ui = candidate[rand]
        candidate.remove(ui)
        H.add(ui)
        rand = random.random()
        if rand < graph.nodes_acceptance[ui]:
            user_participant[ui] = 0
            update(graph, edge_realization, user_participant, k, ui)
        if i % step == 0:
            profit = findProfit(user_participant, R)
            stat[i] = profit
    return stat

def maxDegree(graph, R, b, k):
    H = set()
    edge_realization = {}
    for edge in graph.edges:
        edge_realization[edge] = '?'
    user_participant = {}
    for v in graph.nodes:
        user_participant[v] = k + 1

    node_degree = {}
    for node in graph.nodes:
        node_degree[node] = len(graph.get_neighbor(node))
    node_degree = sorted(node_degree.items(), key=lambda item: item[1], reverse=True)

    step = b / 6
    stat = {}

    for i in range(1, b + 1):
        ui = node_degree[i - 1][0]
        H.add(ui)
        rand = random.random()
        if rand < graph.nodes_acceptance[ui]:
            user_participant[ui] = 0
            update(graph, edge_realization, user_participant, k, ui)
        if i % step == 0:
            profit = findProfit(user_participant, R)
            stat[i] = profit
    return stat

def maxProb(graph, R, b, k):
    H = set()
    edge_realization = {}
    for edge in graph.edges:
        edge_realization[edge] = '?'
    user_participant = {}
    for v in graph.nodes:
        user_participant[v] = k + 1

    node_prob = copy.deepcopy(graph.nodes_acceptance)
    node_prob = sorted(node_prob.items(), key=lambda item: item[1], reverse=True)

    step = b / 6
    stat = {}

    for i in range(1, b + 1):
        ui = node_prob[i - 1][0]
        H.add(ui)
        rand = random.random()
        if rand < graph.nodes_acceptance[ui]:
            user_participant[ui] = 0
            update(graph, edge_realization, user_participant, k, ui)
        if i % step == 0:
            profit = findProfit(user_participant, R)
            stat[i] = profit
    return stat


if __name__ == '__main__':
    path = "ca-netscience.txt"
    graph = readGraph(path, 0.5)

    graph.nodes_acceptance = {1: 0.3579751355799503, 2: 0.586569001475359, 3: 0.16113300460829805, 4: 0.09772843937623965, 5: 0.3418094415661126,
     6: 0.5983599010446605, 7: 0.12763744195626203, 8: 0.29350323477873597, 9: 0.5056955652792037,
     10: 0.5475740414743019, 11: 0.7323720435985012, 12: 0.5966948910333452, 13: 0.6488914701892666,
     14: 0.28507153797889284, 15: 0.486570661240894, 16: 0.6170869565606083, 17: 0.9836251445798186,
     18: 0.2323520761257868, 19: 0.9921138745645454, 20: 0.5969926102524147, 21: 0.6289260148261814,
     22: 0.040115609924778806, 23: 0.27491142881865505, 24: 0.4044675134623932, 25: 0.5692346333691657,
     26: 0.4812537498207342, 27: 0.09668166165176972, 28: 0.8630013393392868, 29: 0.9172074043111804,
     30: 0.0028690885414724976, 31: 0.03583892223252638, 32: 0.13528452495086518, 33: 0.8847596479846185,
     34: 0.8771761807986242, 35: 0.4245290361378481, 36: 0.7143769379405892, 37: 0.8409038325480818,
     38: 0.10231288283371942, 39: 0.44479293790700203, 40: 0.725630399959659, 41: 0.5423543065903947,
     42: 0.17451774177601442, 43: 0.17335022896417196, 44: 0.2986470965076262, 45: 0.5936369945412103,
     46: 0.6203111268892563, 47: 0.42574370587921506, 48: 0.005251647355656641, 49: 0.1460808990378436,
     50: 0.9768892543687964, 51: 0.7693519413913698, 52: 0.7448444453030808, 53: 0.24254523382548576,
     54: 0.034299637879796396, 55: 0.9676049465731335, 56: 0.6977321097940066, 57: 0.6493442965287586,
     58: 0.7027466870431739, 59: 0.019130718985492012, 60: 0.42466741700878585, 61: 0.4328877263103186,
     62: 0.49945814301533853, 63: 0.18239357112306154, 64: 0.8408913893044835, 65: 0.5063182356692617,
     66: 0.097421841841978, 67: 0.3983364154054754, 68: 0.4515579434792051, 69: 0.3091034516953456,
     70: 0.8116767500256644, 71: 0.5996453883225259, 72: 0.5978839014748852, 73: 0.3661436774159018,
     74: 0.30156405743337156, 75: 0.4047674532311103, 76: 0.7451584255531173, 77: 0.8476178921250329,
     78: 0.7472413053467365, 79: 0.3664961075004469, 80: 0.463018158035182, 81: 0.041376504068931785,
     82: 0.30704163916189875, 83: 0.7241882002078389, 84: 0.44562351115077925, 85: 0.5028560430278596,
     86: 0.13507029407470672, 87: 0.5377016331369606, 88: 0.4304031169033218, 89: 0.24532888573485678,
     90: 0.9741656780059932, 91: 0.9939490792201933, 92: 0.805341032310733, 93: 0.7327111434112683,
     94: 0.8387867338485169, 95: 0.014285992335247633, 96: 0.4295620603321233, 97: 0.08264337901225771,
     98: 0.2853256624374566, 99: 0.1428250937384059, 100: 0.3242438073825936, 101: 0.5224047772122389,
     102: 0.5761245769431286, 103: 0.9922894918049642, 104: 0.6089843902728194, 105: 0.10012511782992184,
     106: 0.47836029203838515, 107: 0.19470103004071626, 108: 0.5062212208071061, 109: 0.09594708696436682,
     110: 0.9947314206715473, 111: 0.5131276423723354, 112: 0.198074702983972, 113: 0.8565410208979691,
     114: 0.7694851613855082, 115: 0.2736668761057369, 116: 0.1683334089154822, 117: 0.3396443216087931,
     118: 0.6554846616101818, 119: 0.3921151856283931, 120: 0.4531531480183728, 121: 0.7045746197486064,
     122: 0.9384800487747781, 123: 0.5149528066623059, 124: 0.8034384085967147, 125: 0.023461937043216086,
     126: 0.4098515850069163, 127: 0.5962301676643795, 128: 0.13279682754790478, 129: 0.9077610196478977,
     130: 0.2797416234799145, 131: 0.054808863570281474, 132: 0.7736130606234987, 133: 0.9570223603299468,
     134: 0.43430289412341583, 135: 0.5404215388077008, 136: 0.6585480333111076, 137: 0.5690324911505801,
     138: 0.09132315873110475, 139: 0.8990828318827321, 140: 0.5391528851949544, 141: 0.0398570519362037,
     142: 0.5684896436855678, 143: 0.8906173851437501, 144: 0.4764834163266427, 145: 0.0248485497487424,
     146: 0.3115108384783216, 147: 0.8931727587843286, 148: 0.04504352123132982, 149: 0.20803553430190935,
     150: 0.31461960286100743, 151: 0.36094295840548674, 152: 0.7271018247305094, 153: 0.36542927548716997,
     154: 0.37451545154591315, 155: 0.24160808890331842, 156: 0.9610998195917135, 157: 0.7272130887992561,
     158: 0.6197249392211004, 159: 0.8146822422083465, 160: 0.5332843382292314, 161: 0.7419456640951212,
     162: 0.11946347329353557, 163: 0.7446012665466568, 164: 0.5588358381766008, 165: 0.8970717172265013,
     166: 0.6761795515066662, 167: 0.6906405785162226, 168: 0.33593492516283907, 169: 0.05449424162531902,
     170: 0.38228284538737245, 171: 0.09944370800458913, 172: 0.11412718719292925, 173: 0.8919698281579176,
     174: 0.5570959451815464, 175: 0.0707403180080951, 176: 0.994483118073468, 177: 0.976777773649059,
     178: 0.2871013391789614, 179: 0.04008077600541249, 180: 0.8859008145729939, 181: 0.5503059798554267,
     182: 0.8043160963595924, 183: 0.21155666798810202, 184: 0.9543371328294873, 185: 0.8604364400078304,
     186: 0.1503921768936799, 187: 0.6864723322357937, 188: 0.1771785345274406, 189: 0.8442126265238721,
     190: 0.013650768678056702, 191: 0.05940892055123548, 192: 0.37957095600945323, 193: 0.150640821477663,
     194: 0.2458505711753648, 195: 0.7930113043513085, 196: 0.9155355467872816, 197: 0.8657982777087756,
     198: 0.08811072209781756, 199: 0.3872171780478739, 200: 0.7558993196592372, 201: 0.13696353956655016,
     202: 0.7575198853294737, 203: 0.453756517585868, 204: 0.15992091334735414, 205: 0.14977256463641775,
     206: 0.46483689920374904, 207: 0.06966191870265015, 208: 0.6970153510903067, 209: 0.6439054063122034,
     210: 0.6197524069159379, 211: 0.8712493890339071, 212: 0.6875279567220598, 213: 0.9097198693938132,
     214: 0.8533925905879475, 215: 0.5423139036582998, 216: 0.9767770852088657, 217: 0.1272652000649075,
     218: 0.9003043609507536, 219: 0.6437681897382369, 220: 0.5905338751085675, 221: 0.1634097367175219,
     222: 0.23899334234517366, 223: 0.021264438552421105, 224: 0.5992147745874024, 225: 0.1511403312562335,
     226: 0.7437349978959257, 227: 0.6080201160925363, 228: 0.48913149665722644, 229: 0.22806115666159588,
     230: 0.1536535699536804, 231: 0.8334621520599902, 232: 0.5110271155392495, 233: 0.3798647655505427,
     234: 0.3767664793673373, 235: 0.9473940225737421, 236: 0.180700633997533, 237: 0.03810661366822732,
     238: 0.13812580830746968, 239: 0.13931645998936715, 240: 0.5693029460903091, 241: 0.34146083821011697,
     242: 0.0763692899629631, 243: 0.657387525680433, 244: 0.28495805190881984, 245: 0.5938997536671136,
     246: 0.7798023616874662, 247: 0.6856923497850246, 248: 0.49654570064500814, 249: 0.9064115254548155,
     250: 0.5515956089552383, 251: 0.45566314924469276, 252: 0.11886703275080213, 253: 0.006552910612084073,
     254: 0.14539761451103184, 255: 0.6924819703092744, 256: 0.6528663758414572, 257: 0.510991754884757,
     258: 0.6293622336628278, 259: 0.2964309020863348, 260: 0.8923076416366603, 261: 0.7197028021430524,
     262: 0.4697979427725598, 263: 0.300985571700904, 264: 0.9061680020327423, 265: 0.4929724149611745,
     266: 0.7875639316338297, 267: 0.8208092130769448, 268: 0.24170015185103044, 269: 0.3753124188588326,
     270: 0.48384693528309564, 271: 0.7890071482053805, 272: 0.5736683674470668, 273: 0.48669514760928434,
     274: 0.9494923927899226, 275: 0.8852262155948332, 276: 0.9621602970648564, 277: 0.14590056243188498,
     278: 0.9787980405672768, 279: 0.5170644422476134, 280: 0.5246822548432195, 281: 0.5149817843204764,
     282: 0.07485709883141956, 283: 0.24985557466561215, 284: 0.6264437867290957, 285: 0.08160846597346028,
     286: 0.34061871003538724, 287: 0.38087875651634984, 288: 0.39013544772283126, 289: 0.5290039006672969,
     290: 0.9821961459148435, 291: 0.2438482712154506, 292: 0.16005171171972288, 293: 0.6663549953204332,
     294: 0.2537533841313664, 295: 0.3922577757667751, 296: 0.02769284795212479, 297: 0.35066295741062925,
     298: 0.5739712148914811, 299: 0.680354087747996, 300: 0.4659919854072868, 301: 0.22859057125820714,
     302: 0.44860645280762546, 303: 0.3397648029999881, 304: 0.2960776432316772, 305: 0.668128870600747,
     306: 0.08808483612442908, 307: 0.6152435274561385, 308: 0.3311548784919872, 309: 0.12221129349490756,
     310: 0.5473893963328723, 311: 0.6034816595845236, 312: 0.24502362891595753, 313: 0.8893715222149774,
     314: 0.20549761461661264, 315: 0.2810588603640476, 316: 0.05813256962179514, 317: 0.16454542585985454,
     318: 0.48152343920312524, 319: 0.12576215967483784, 320: 0.8774206125391842, 321: 0.1377871599380185,
     322: 0.7904225069307761, 323: 0.5242506057765137, 324: 0.9749862675680185, 325: 0.6447080223109912,
     326: 0.22516668439581422, 327: 0.18630006070001692, 328: 0.46738718687608727, 329: 0.22194764325088912,
     330: 0.786640038803781, 331: 0.46048391574044656, 332: 0.2699314406490805, 333: 0.04113641659099909,
     334: 0.7480386728249028, 335: 0.4417774891811982, 336: 0.24668899862817495, 337: 0.5357466367672004,
     338: 0.6126770687422634, 339: 0.8209476871214387, 340: 0.4264385293239388, 341: 0.6611356460608602,
     342: 0.4960052271281762, 343: 0.03585749368570179, 344: 0.8141317620204103, 345: 0.18059954826437696,
     346: 0.2441367507659814, 347: 0.22547137769687553, 348: 0.02795504402672866, 349: 0.1300904869031777,
     350: 0.8760514265551363, 351: 0.17552861536375308, 352: 0.14201709855247957, 353: 0.42282684834431306,
     354: 0.017156017810746493, 355: 0.23478352953785864, 356: 0.5616520216855978, 357: 0.20507665615529347,
     358: 0.10750971991436198, 359: 0.2700152272021831, 360: 0.274886912773218, 361: 0.8198851216186327,
     362: 0.7292892147329731, 363: 0.3255374271279682, 364: 0.9057963771812186, 365: 0.21214252406784762,
     366: 0.23041777903562144, 367: 0.9512575870660782, 368: 0.025575941837384764, 369: 0.03295179768235568,
     370: 0.047205255535567536, 371: 0.8920876557675482, 372: 0.7754244968370676, 373: 0.2623210359937018,
     374: 0.46374283540597394, 375: 0.640726691553876, 376: 0.5847097913720873, 377: 0.025912563309091974,
     378: 0.6915111535514245, 379: 0.4537268940294117}

    # R = [8, 6, 4, 0]
    # t = 10
    # listt = []
    # listt_time = []
    # b = 60
    # for i in range(1, t + 1):
    #     print("times = " + str(i))
    #     statistics, ttime = adaptiveInvitation(graph, R, b, 2)
    #     listt.append(statistics)
    #     listt_time.append(ttime)
    #     print(statistics)
    # step = b / 6
    # average = {}
    # for i in range(1, 7):
    #     k = int(step * i)
    #     sum = 0
    #     for statistics in listt:
    #         sum += statistics[k]
    #     average[k] = sum / t
    # print("average = " + str(average))
    # average_time = {}
    # for i in range(1, 7):
    #     k = int(step * i)
    #     sum = 0
    #     for tt in listt_time:
    #         sum += tt[k]
    #     average_time[k] = sum / t
    # print("average time = " + str(average_time))
    # std = {}
    # for i in range(1, 7):
    #     k = int(step * i)
    #     sum = 0
    #     for statistics in listt:
    #         sum += (statistics[k] - average[k])**2
    #     std[k] = math.sqrt(sum / t)
    # print("std = " + str(std))


    # print("--------------")
    R = [8, 6, 4, 2, 0]
    t = 10
    listt = []
    listt_time = []
    b = 60
    for i in range(1, t + 1):
        print("times = " + str(i))
        statistics, ttime = adaptiveInvitation(graph, R, b, 3)
        listt.append(statistics)
        listt_time.append(ttime)
        print(statistics)
    step = b / 6
    average = {}
    for i in range(1, 7):
        k = int(step * i)
        sum = 0
        for statistics in listt:
            sum += statistics[k]
        average[k] = sum / t
    print("average = " + str(average))
    average_time = {}
    for i in range(1, 7):
        k = int(step * i)
        sum = 0
        for tt in listt_time:
            sum += tt[k]
        average_time[k] = sum / t
    print("average time = " + str(average_time))
    std = {}
    for i in range(1, 7):
        k = int(step * i)
        sum = 0
        for statistics in listt:
            sum += (statistics[k] - average[k])**2
        std[k] = math.sqrt(sum / t)
    print("std = " + str(std))


