/**
*
* Copyright (C) 2014-2017    Andrei Novikov (pyclustering@yandex.ru)
*
* GNU_PUBLIC_LICENSE
*   pyclustering is free software: you can redistribute it and/or modify
*   it under the terms of the GNU General Public License as published by
*   the Free Software Foundation, either version 3 of the License, or
*   (at your option) any later version.
*
*   pyclustering is distributed in the hope that it will be useful,
*   but WITHOUT ANY WARRANTY; without even the implied warranty of
*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*   GNU General Public License for more details.
*
*   You should have received a copy of the GNU General Public License
*   along with this program.  If not, see <http://www.gnu.org/licenses/>.
*
*/

#include <string>
#include <fstream>
#include <sstream>

#include "ccore.h"

#include "cluster/hsyncnet.hpp"
#include "cluster/xmeans.hpp"

#include "tsp/ant_colony.hpp"

#include "utils.hpp"


using namespace container;


void * hsyncnet_create_network(const data_representation * const sample, 
                               const unsigned int number_clusters, 
                               const unsigned int initial_phases,
                               const unsigned int initial_neighbors,
                               const double increase_persent) {

	std::vector<std::vector<double> > * dataset = read_sample(sample);	/* belongs to hsyncnet */
	return (void *) new hsyncnet(dataset, number_clusters, (initial_type) initial_phases, initial_neighbors, increase_persent);
}

void hsyncnet_destroy_network(const void * pointer_network) {
	if (pointer_network != NULL) {
		delete (hsyncnet *) pointer_network;
	}
}

void * hsyncnet_process(const void * pointer_network, const double order, const unsigned int solver, const bool collect_dynamic) {
	hsyncnet * network = (hsyncnet *) pointer_network;

	hsyncnet_analyser * analyser = new hsyncnet_analyser();
	network->process(order, (solve_type) solver, collect_dynamic, *analyser);

	return (void *) analyser;
}

void hsyncnet_analyser_destroy(const void * pointer_analyser) {
	if (pointer_analyser != NULL) {
		delete (hsyncnet_analyser *) pointer_analyser;
	}
}


/////////////////////////////////////////////////////////////////////////////
//                  Ant Colony functions
//
tsp_result * ant_colony_tsp_process_get_result(std::shared_ptr<city_distance::distance_matrix>& dist, const ant::ant_colony_tsp_params * algorithm_params) {
       // Algorithm params
       using AntAPI = ant::ant_colony_TSP_params_initializer;
       auto algo_params = ant::ant_colony_TSP_params::make_param
           (AntAPI::Q_t{ algorithm_params->q }
               , AntAPI::Ro_t{ algorithm_params->ro }
               , AntAPI::Alpha_t{ algorithm_params->alpha }
               , AntAPI::Beta_t{ algorithm_params->beta }
               , AntAPI::Gamma_t{ algorithm_params->gamma }
               , AntAPI::InitialPheramone_t{ algorithm_params->initial_pheramone }
               , AntAPI::Iterations_t{ algorithm_params->iterations }
               , AntAPI::CountAntsInIteration_t{ algorithm_params->count_ants_in_iteration }
       );

       // process()
       ant::ant_colony ant_algo{ dist, algo_params };
       auto algo_res = ant_algo.process();

       // create result for python
       tsp_result * result = new tsp_result();

       // init path length
       result->path_length = algo_res->path_length;

       // create array to stored cities in the path
       result->objects_sequence = new unsigned int[algo_res->shortest_path.size()];
       result->size = algo_res->shortest_path.size();

       // copy cities to result
       for (std::size_t object_number = 0; object_number < algo_res->shortest_path.size(); ++object_number) {
           result->objects_sequence[object_number] = algo_res->shortest_path[object_number];
       }

       return result;
}

tsp_result * ant_colony_tsp_process_by_matrix(const tsp_matrix * objects_coord, const void * ant_colony_parameters) {
    std::vector<std::vector<double>> matrix;

    matrix.resize(objects_coord->size);

    for (std::size_t i = 0; i < matrix.size(); ++i) {
        matrix[i].resize(objects_coord->size);

        for (std::size_t j = 0; j < matrix[i].size(); ++j) {
            matrix[i][j] = objects_coord->data[i][j];
        }
    }

    auto dist = city_distance::distance_matrix::make_city_distance_matrix (matrix);
    return ant_colony_tsp_process_get_result(dist, static_cast<const ant::ant_colony_tsp_params *>(ant_colony_parameters) );
}


tsp_result * ant_colony_tsp_process(const tsp_objects * objects_coord, const void * ant_colony_parameters) {
    const ant::ant_colony_tsp_params * algorithm_params = (const ant::ant_colony_tsp_params *) ant_colony_parameters;
    std::vector<city_distance::object_coordinate> cities;

    for (std::size_t city_num = 0; city_num < objects_coord->size / objects_coord->dimention; ++city_num) {
        std::vector<double> v(objects_coord->dimention);

        for (std::size_t dim = 0; dim < objects_coord->dimention; ++dim) {
            v[dim] = objects_coord->data[city_num*objects_coord->dimention + dim];
        }

        cities.push_back(std::move(v));
    }

    auto dist = city_distance::distance_matrix::make_city_distance_matrix (cities);
    return ant_colony_tsp_process_get_result(dist, algorithm_params);
}


void ant_colony_tsp_destroy(const void * result) {
    if (result != nullptr) {
        delete [] ((tsp_result *) result)->objects_sequence;
        delete (tsp_result *) result;
    }
}
//
//                  End Ant colony functions
/////////////////////////////////////////////////////////////////////////////
