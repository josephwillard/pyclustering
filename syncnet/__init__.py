from nnet.sync import *;

from support import draw_clusters;
from support import read_sample;

class syncnet(sync_network):
    _osc_loc = None;
    
    _ena_conn_weight = False;
    _conn_weight = None;
    
    def __init__(self, source_data, conn_repr = conn_represent.MATRIX, radius = None, initial_phases = initial_type.RANDOM_GAUSSIAN, enable_conn_weight = False):
        sample = None;
        if ( isinstance(source_data, str) ):
            file = open(source_data, 'r');
            sample = [[float(val) for val in line.split()] for line in file];
            file.close();
        else:
            sample = source_data;
        
        super().__init__(len(sample), 1, False, conn_type.NONE, initial_phases);
        
        self._ena_conn_weight = enable_conn_weight;
        self._osc_loc = sample;
        self._conn_represent = conn_repr;

        # Connections will be represent by lists.
        if (conn_repr == conn_represent.MATRIX):
            self._osc_conn = [[0] * self._num_osc for index in range(0, self._num_osc, 1)];
            
        elif (conn_repr == conn_represent.LIST):
            self._osc_conn = [[] for index in range(0, self._num_osc, 1)];
            
        else:
            raise NameError("Unknown type of representation of coupling between oscillators");
        
        # Create connections.
        if (radius is not None):
            self._create_connections(radius);
    

    def _create_connections(self, radius):
        "Create connections between oscillators in line with input radius of connectivity"
        
        "(in) radius    - connectivity radius between oscillators"
        if (self._ena_conn_weight is True):
            self._conn_weight = [[0] * self._num_osc for index in range(0, self._num_osc, 1)];
        
        maximum_distance = 0;
        minimum_distance = numpy.Inf;
        
        # Create connections
        for i in range(0, self._num_osc, 1):
            for j in range(i + 1, self._num_osc, 1):                 
                    dist = euclidean_distance(self._osc_loc[i], self._osc_loc[j]);
                    
                    if (self._ena_conn_weight is True):
                        self._conn_weight[i][j] = dist;
                        self._conn_weight[j][i] = dist;
                        
                        if (dist > maximum_distance): maximum_distance = dist;
                        if (dist < minimum_distance): minimum_distance = dist;
                    
                    if (dist <= radius):
                        if (self._conn_represent == conn_represent.LIST):
                            self._osc_conn[i].append(j);
                            self._osc_conn[j].append(i);
                        else:
                            self._osc_conn[i][j] = True;
                            self._osc_conn[j][i] = True;
        
        if (self._ena_conn_weight is True):
            multiplier = 1; 
            subtractor = 0;
            
            if (maximum_distance != minimum_distance):
                multiplier = (maximum_distance - minimum_distance);
                subtractor = minimum_distance;
            
            for i in range(0, self._num_osc, 1):
                for j in range(i + 1, self._num_osc, 1):
                    value_conn_weight = (self._conn_weight[i][j] - subtractor) / multiplier;
                    
                    self._conn_weight[i][j] = value_conn_weight;
                    self._conn_weight[j][i] = value_conn_weight;


    def process(self, radius = None, order = 0.998, solution = solve_type.FAST, collect_dynamic = False):
        "Network is trained via achievement sync state between the oscillators using the radius of coupling"
        
        "(in) radius            - connectivity radius for simulation, if it is specified then connections will be recreated"
        "(in) order             - order of synchronization that is used as indication for stopping processing"
        "(in) solution          - specified type of solving diff. equation"
        "(in) collect_dynamic   - specified requirement to collect whole dynamic of the network"
        
        "Return last values of simulation time and phases of oscillators as a tuple if collect_dynamic is False, and whole dynamic"
        "if collect_dynamic is True. Format of returned value: (simulation_time, oscillator_phases)."
        # Create connections in line with input radius
        if (radius != None):
            self._create_connections(radius);
        
        return self.simulate_dynamic(order, solution, collect_dynamic);
    
    
    def phase_kuramoto(self, teta, t, argv):
        "Overrided method for calculation of oscillator phase"
        
        "(in) teta     - current value of phase"
        "(in) t        - time (can be ignored)"
        "(in) argv     - index of oscillator whose phase represented by argument teta"
        
        "Return new value of phase of oscillator with index 'argv'"
        index = argv;   # index of oscillator
        phase = 0;      # phase of a specified oscillator that will calculated in line with current env. states.
        
        neighbors = self.get_neighbors(index);
        for k in neighbors:
            conn_weight = 1;
            if (self._ena_conn_weight is True):
                conn_weight = self._conn_weight[index][k];
                
            phase += conn_weight * self._weight * math.sin(self._cluster * (self._phases[k] - teta));
        
        divider = len(neighbors);
        if (divider == 0): 
            divider = 1;
            
        return ( self._freq[index] + (phase / divider) );   


    def get_clusters(self, eps = 0.1):
        "Return list of clusters in line with state of ocillators (phases)."
        
        "(in) eps     - tolerance level that define maximal difference between phases of oscillators in one cluster"
        
        "Return list of clusters, for example [ [cluster1], [cluster2], ... ]"
        return self.allocate_sync_ensembles(eps);
    
    
    def show_network(self):
        "Show connections in the network. It supports only 2-d and 3-d representation."
        dimension = len(self._osc_loc[0]);
        if ( (dimension != 3) and (dimension != 2) ):
            raise NameError('Network that is located in different from 2-d and 3-d dimensions can not be represented');
        
        from matplotlib.font_manager import FontProperties;
        from matplotlib import rcParams;
    
        rcParams['font.sans-serif'] = ['Arial'];
        rcParams['font.size'] = 12;

        fig = plt.figure();
        axes = None;
        if (dimension == 2):
            axes = fig.add_subplot(111);
        elif (dimension == 3):
            axes = fig.gca(projection='3d');
        
        surface_font = FontProperties();
        surface_font.set_name('Arial');
        surface_font.set_size('12');
        
        for i in range(0, self.num_osc, 1):
            if (dimension == 2):
                axes.plot(self._osc_loc[i][0], self._osc_loc[i][1], 'bo');  
                if (self._conn_represent == conn_represent.MATRIX):
                    for j in range(i, self._num_osc, 1):    # draw connection between two points only one time
                        if (self.has_connection(i, j) == True):
                            axes.plot([self._osc_loc[i][0], self._osc_loc[j][0]], [self._osc_loc[i][1], self._osc_loc[j][1]], 'b-', linewidth = 0.5);    
                            
                else:
                    for j in self.get_neighbors(i):
                        if ( (self.has_connection(i, j) == True) and (i > j) ):     # draw connection between two points only one time
                            axes.plot([self._osc_loc[i][0], self._osc_loc[j][0]], [self._osc_loc[i][1], self._osc_loc[j][1]], 'b-', linewidth = 0.5);    
            
            elif (dimension == 3):
                axes.scatter(self._osc_loc[i][0], self._osc_loc[i][1], self._osc_loc[i][2], c = 'b', marker = 'o');
                
                if (self._conn_represent == conn_represent.MATRIX):
                    for j in range(i, self._num_osc, 1):    # draw connection between two points only one time
                        if (self.has_connection(i, j) == True):
                            axes.plot([self._osc_loc[i][0], self._osc_loc[j][0]], [self._osc_loc[i][1], self._osc_loc[j][1]], [self._osc_loc[i][2], self._osc_loc[j][2]], 'b-', linewidth = 0.5);
                        
                else:
                    for j in self.get_neighbors(i):
                        if ( (self.has_connection(i, j) == True) and (i > j) ):     # draw connection between two points only one time
                            axes.plot([self._osc_loc[i][0], self._osc_loc[j][0]], [self._osc_loc[i][1], self._osc_loc[j][1]], [self._osc_loc[i][2], self._osc_loc[j][2]], 'b-', linewidth = 0.5);
                               
        plt.grid();
        plt.show();
    
