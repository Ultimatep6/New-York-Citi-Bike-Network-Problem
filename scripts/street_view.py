
import pandas as pd

def read_data(station_csv_path, results_csv_path):

    stations = pd.read_csv(station_csv_path)

    consumer_stations = stations[stations['net_flow'] < 0]
    supplier_stations = stations[stations['net_flow'] > 0]
    warehouse_stations = stations[stations['station_name'] == 'Warehouse']
    some_stations = pd.concat([consumer_stations, supplier_stations, warehouse_stations])

    results = pd.read_csv(results_csv_path)

    visited_paths = results[results['value'] == 1]

    path = {bus: [] for bus in results['bus'].unique()}

    for bus in results['bus'].unique():
        df_bus_stations = visited_paths[visited_paths['bus'] == bus].copy()
        
        if df_bus_stations.empty:
            continue
        
        start = 'Warehouse'
        route = [start]
        used_edges = set()
        
        while True:
            # Find next edge that hasn't been used yet
            next_stations = df_bus_stations[
                (df_bus_stations['from'] == start) & 
                (~df_bus_stations.apply(lambda x: (x['from'], x['to']) in used_edges, axis=1))
            ]
            
            if next_stations.empty:
                break
                
            next_station = next_stations.iloc[0]['to']
            route.append(next_station)
            used_edges.add((start, next_station))
            start = next_station
        
        path[bus] = route

    # Convert routes to coordinates
    path_coords = {bus: [] for bus in results['bus'].unique()}
    for bus in results['bus'].unique():
        if len(path[bus]) > 0:
            for station in path[bus]:
                station_info = some_stations[some_stations['station_name'] == station].iloc[0]
                path_coords[bus].append([station_info['latitude'], station_info['longitude']])
    
    # Validation: Print route statistics
    print("\n" + "="*80)
    print("ROUTE VALIDATION")
    print("="*80)
    for bus in results['bus'].unique():
        bus_edges = visited_paths[visited_paths['bus'] == bus]
        if not bus_edges.empty:
            print(f"\n{bus}:")
            print(f"  Total edges in solution: {len(bus_edges)}")
            print(f"  Stations in reconstructed route: {len(path[bus])}")
            print(f"  Expected edges from route: {len(path[bus]) - 1}")
            print(f"  Route: {' → '.join(path[bus])}")
            
            if len(path[bus]) - 1 != len(bus_edges):
                print(f"  ⚠️  WARNING: Mismatch! Missing {len(bus_edges) - (len(path[bus]) - 1)} edges")
        else:
            print(f"\n{bus}: Not used (0 edges)")
    print("="*80 + "\n")

    return some_stations, warehouse_stations, consumer_stations, supplier_stations, path_coords 

def draw_map(some_stations, warehouse_stations, consumer_stations, supplier_stations,
             path_coords):

    avg_location = [some_stations['latitude'].mean(), some_stations['longitude'].mean()]
    print("Average location (lat, long):", avg_location)

    import folium

    my_map3 = folium.Map(location = [avg_location[0], avg_location[1]], zoom_start = 12)

    for idx, row in consumer_stations.iterrows():
        folium.Marker([row['latitude'], row['longitude']],
                    popup = f"Consumer Station: {row['station_name']}<br>Net Flow: {row['net_flow']}").add_to(my_map3)

    for idx, row in supplier_stations.iterrows():
        folium.Marker([row['latitude'], row['longitude']],
                    popup = f"Supplier Station: {row['station_name']}<br>Net Flow: {row['net_flow']}",
                    icon=folium.Icon(color='green')).add_to(my_map3)

    for idx, row in warehouse_stations.iterrows():
        folium.Marker([row['latitude'], row['longitude']],
                    popup = f"Warehouse Station: {row['station_name']}<br>Net Flow: {row['net_flow']}",
                    icon=folium.Icon(color='red', icon='info-sign')).add_to(my_map3)
        
    # Draw routes with direction arrows
    colors = ["blue", "red", "green", "purple", "orange", "darkred", "darkblue", "darkgreen"]
    for idx, (bus, coords) in enumerate(path_coords.items()):
        if len(coords) > 1:
            color = colors[idx % len(colors)]
            # Draw the route line
            folium.PolyLine(
                coords, 
                color=color, 
                weight=3, 
                opacity=0.8,
                popup=f"{bus} route ({len(coords)} stops)"
            ).add_to(my_map3)
            
            # Add arrows to show direction (every 2-3 segments to avoid clutter)
            for i in range(0, len(coords) - 1, max(1, len(coords) // 5)):
                folium.PolyLine(
                    [coords[i], coords[i + 1]],
                    color=color,
                    weight=3,
                    opacity=0.8,
                    popup=f"{bus}: Stop {i} → {i+1}"
                ).add_to(my_map3)
                
                # Add a small circle marker to show sequence
                folium.CircleMarker(
                    coords[i],
                    radius=4,
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.6,
                    popup=f"{bus} - Stop #{i}"
                ).add_to(my_map3)


    return my_map3

# some_stations, warehouse, consumers, suppliers, path_coords = read_data(
#     r"./processed_data/some_stations_small.csv",
#     r"./results/solutionV2_test.csv"
# )

# my_map = draw_map(some_stations, warehouse, consumers, suppliers, path_coords)
# my_map.save("./results/street_view.html")