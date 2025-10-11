#!/usr/bin/env python3
"""
Simple flight data viewer for CSV files in outputs directory - IMPROVED VERSION
"""

import os
from pathlib import Path

import pandas as pd
import streamlit as st


def extract_airports_from_filename(filename):
	"""Extract departure and arrival airports from filename pattern like 'dep_OPO_NRT_<date>__arr_NRT_OPO_<date>'"""
	try:
		if '__arr_' in filename:
			dep_part = filename.split('__arr_')[0]
			# Extract from dep_FROM_TO_date pattern
			dep_parts = dep_part.replace('dep_', '').split('_')
			if len(dep_parts) >= 2:
				dep_from = dep_parts[0]  # OPO
				dep_to = dep_parts[1]    # NRT
				return dep_from, dep_to
	except:
		pass
	return None, None

def extract_departure_date(filename):
	"""Extract departure date from filename for sorting purposes"""
	try:
		if '__arr_' in filename:
			dep_part = filename.split('__arr_')[0]
			dep_parts = dep_part.replace('dep_', '').split('_')
			if len(dep_parts) >= 3:
				dep_date = dep_parts[2]
				from datetime import datetime

				return datetime.strptime(dep_date, '%Y-%m-%d')
	except:
		pass
	# Return a very old date as fallback to sort unknown formats last
	from datetime import datetime

	return datetime(1900, 1, 1)


def create_friendly_name(filename):
	"""Convert filename like 'dep_OPO_MAD_2025-12-06__arr_MAD_OPO_2025-12-09' to friendly name"""
	try:
		# Parse the filename
		if '__arr_' in filename:
			dep_part, arr_part = filename.split('__arr_')

			# Extract departure info
			dep_parts = dep_part.replace('dep_', '').split('_')
			if len(dep_parts) >= 3:
				dep_from = dep_parts[0]
				dep_to = dep_parts[1]
				dep_date = dep_parts[2]

			# Extract arrival info
			arr_parts = arr_part.split('_')
			if len(arr_parts) >= 3:
				arr_date = arr_parts[2]

				# Format dates to be more readable
				from datetime import datetime

				try:
					dep_dt = datetime.strptime(dep_date, '%Y-%m-%d')
					arr_dt = datetime.strptime(arr_date, '%Y-%m-%d')

					dep_formatted = dep_dt.strftime('%b %d')
					arr_formatted = arr_dt.strftime('%b %d')

					return f'{dep_from} → {dep_to} ({dep_formatted} - {arr_formatted})'
				except:
					return f'{dep_from} → {dep_to} ({dep_date} - {arr_date})'

		# Fallback for other formats
		return filename.replace('_', ' ').replace('dep ', '').replace('arr ', '')
	except:
		return filename


def load_csv_files(outputs_dir='outputs'):
	"""Load all CSV files from the outputs directory"""
	csv_files = {}

	if not os.path.exists(outputs_dir):
		st.error(f"Directory '{outputs_dir}' not found!")
		return csv_files

	csv_paths = list(Path(outputs_dir).glob('*.csv'))

	if not csv_paths:
		st.warning(f"No CSV files found in '{outputs_dir}' directory!")
		return csv_files

	for csv_path in csv_paths:
		try:
			df = pd.read_csv(csv_path)
			# Use filename without extension as key
			original_filename = csv_path.stem
			friendly_name = create_friendly_name(original_filename)
			csv_files[friendly_name] = df

		except Exception as e:
			st.error(f'Error loading {csv_path.name}: {e}')

	return csv_files


def format_currency(value):
	"""Format currency values"""
	try:
		return f'€{float(value):.2f}'
	except:
		return value


def format_duration(value):
	"""Format duration values properly"""
	try:
		hours = float(value)
		# Convert to hours and minutes
		total_minutes = int(hours * 60)
		h = total_minutes // 60
		m = total_minutes % 60
		if h > 0 and m > 0:
			return f'{h}h {m}m'
		elif h > 0:
			return f'{h}h'
		else:
			return f'{m}m'
	except:
		return str(value) if value else 'N/A'


def main():
	st.set_page_config(page_title='Flight Data Viewer', page_icon='✈️', layout='wide')

	st.title('✈️ Flight Data Viewer')
	st.markdown('View and analyze flight search results with beautiful cards')

	# Load CSV files
	csv_files = load_csv_files()

	if not csv_files:
		st.stop()

	# Filter and clean data
	for filename, df in csv_files.items():
		# Filter out flights with transfers/layovers (transbordo)
		if 'dep_connections' in df.columns:
			df = df[~df['dep_connections'].str.contains('transbordo', case=False, na=False)]
		if 'arr_connections' in df.columns:
			df = df[~df['arr_connections'].str.contains('transbordo', case=False, na=False)]

		# Remove ID and search date columns
		columns_to_remove = [col for col in df.columns if col.endswith('_id') or 'search_date' in col.lower() or col.startswith('dep_id') or col.startswith('arr_id')]

		df = df.drop(columns=columns_to_remove, errors='ignore')
		csv_files[filename] = df

	# Add flight selection interface
	st.markdown("---")
	st.subheader("🎯 Select Your Flight Route")
	
	col1, col2, col3 = st.columns([1, 1, 2])
	
	with col1:
		departure_airport = st.selectbox(
			"✈️ Departure Airport",
			options=["ALL", "OPO", "LIS", "MAD"],
			index=0,
			help="Select your departure airport or ALL for mixed combinations"
		)
	
	with col2:
		arrival_airport = st.selectbox(
			"🛬 Tokyo Airport",
			options=["ALL", "HND", "NRT"],
			index=0,
			help="Select your arrival airport in Tokyo or ALL for mixed combinations"
		)
	
	with col3:
		if departure_airport == "ALL" and arrival_airport == "ALL":
			st.markdown("**Selected Route:** All Combinations")
			st.markdown("**Including mixed routes:** OPO→NRT+HND→LIS, etc.")
		elif departure_airport == "ALL":
			st.markdown(f"**Selected Route:** Any → {arrival_airport}")
			st.markdown(f"**From any city to:** {arrival_airport} ({'Haneda' if arrival_airport == 'HND' else 'Narita'})")
		elif arrival_airport == "ALL":
			st.markdown(f"**Selected Route:** {departure_airport} → Any")
			st.markdown(f"**From:** {departure_airport} ({'Porto' if departure_airport == 'OPO' else 'Lisbon' if departure_airport == 'LIS' else 'Madrid'}) to any Tokyo airport")
		else:
			st.markdown(f"**Selected Route:** {departure_airport} → {arrival_airport}")
			st.markdown(f"**Route Description:** {departure_airport} ({'Porto' if departure_airport == 'OPO' else 'Lisbon' if departure_airport == 'LIS' else 'Madrid'}) to {arrival_airport} ({'Haneda' if arrival_airport == 'HND' else 'Narita'})")

	# Get all available flight data for mixed combinations
	all_flight_data = []
	available_routes = set()
	
	# Load all CSV files and extract route information
	outputs_dir = Path('outputs')
	for csv_path in outputs_dir.glob('*.csv'):
		try:
			df = pd.read_csv(csv_path)
			if df.empty:
				continue
				
			# Clean the data
			if 'dep_connections' in df.columns:
				df = df[~df['dep_connections'].str.contains('transbordo', case=False, na=False)]
			if 'arr_connections' in df.columns:
				df = df[~df['arr_connections'].str.contains('transbordo', case=False, na=False)]
			
			# Remove ID and search date columns
			columns_to_remove = [col for col in df.columns if col.endswith('_id') or 'search_date' in col.lower() or col.startswith('dep_id') or col.startswith('arr_id')]
			df = df.drop(columns=columns_to_remove, errors='ignore')
			
			# Extract route information from filename
			dep_from, dep_to = extract_airports_from_filename(csv_path.stem)
			if dep_from and dep_to:
				df['dep_from_airport'] = dep_from
				df['dep_to_airport'] = dep_to
				df['source_file'] = create_friendly_name(csv_path.stem)
				df['original_filename'] = csv_path.stem
				
				# Filter based on selection
				include_file = False
				if departure_airport == "ALL" and arrival_airport == "ALL":
					include_file = True
				elif departure_airport == "ALL":
					include_file = (dep_to == arrival_airport)
				elif arrival_airport == "ALL":
					include_file = (dep_from == departure_airport)
				else:
					include_file = (dep_from == departure_airport and dep_to == arrival_airport)
				
				if include_file:
					available_routes.add(f"{dep_from} → {dep_to}")
					all_flight_data.append(df)
					
		except Exception as e:
			st.error(f"Error loading {csv_path.name}: {e}")
	
	if not all_flight_data:
		st.warning(f"No flights found for the selected criteria")
		st.stop()

	# Combine all flight data
	combined_df = pd.concat(all_flight_data, ignore_index=True)
	
	st.markdown("---")
	st.info(f"Found data for routes: {', '.join(sorted(available_routes))}")

	# Create summary table for cheapest flights by duration (9, 10, 11 days only)
	st.subheader("💰 Best Deals by Trip Duration (9, 10, 11 days)")
	
	if 'trip_duration_days' in combined_df.columns and 'total_price' in combined_df.columns:
		# Filter for only 9, 10, 11 day trips
		duration_filter = combined_df['trip_duration_days'].isin([9, 10, 11])
		filtered_duration_df = combined_df[duration_filter]
		
		if not filtered_duration_df.empty:
			# Group by trip duration and find cheapest for each duration
			summary_data = []
			
			for duration in [9, 10, 11]:
				duration_df = filtered_duration_df[filtered_duration_df['trip_duration_days'] == duration]
				if not duration_df.empty:
					cheapest_idx = duration_df['total_price'].idxmin()
					cheapest_row = duration_df.loc[cheapest_idx]
					
					# Get return route info from the data
					return_from = cheapest_row.get('arr_departure_airport', 'N/A')
					return_to = cheapest_row.get('arr_arrival_airport', 'N/A')
					
					summary_data.append({
						'Duration': f"{int(duration)} days",
						'Price': f"€{cheapest_row['total_price']:.0f}",
						'Outbound': f"{cheapest_row['dep_from_airport']} → {cheapest_row['dep_to_airport']}",
						'Return': f"{return_from} → {return_to}" if return_from != 'N/A' else f"{cheapest_row['dep_to_airport']} → {cheapest_row['dep_from_airport']}",
						'Dep Date': pd.to_datetime(cheapest_row['dep_departure_date']).strftime('%b %d') if pd.notna(cheapest_row['dep_departure_date']) else 'N/A',
						'Ret Date': pd.to_datetime(cheapest_row['arr_departure_date']).strftime('%b %d') if pd.notna(cheapest_row['arr_departure_date']) else 'N/A',
						'Out €': f"€{cheapest_row['dep_price']:.0f}" if pd.notna(cheapest_row['dep_price']) else 'N/A',
						'Back €': f"€{cheapest_row['arr_price']:.0f}" if pd.notna(cheapest_row['arr_price']) else 'N/A'
					})
			
			if summary_data:
				summary_df = pd.DataFrame(summary_data)
				
				# Display as a nice table
				st.dataframe(
					summary_df,
					use_container_width=True,
					hide_index=True,
					column_config={
						"Duration": st.column_config.TextColumn("🗓️ Duration", width="small"),
						"Price": st.column_config.TextColumn("💰 Total", width="small"),
						"Outbound": st.column_config.TextColumn("🛫 Outbound Route", width="medium"),
						"Return": st.column_config.TextColumn("🛬 Return Route", width="medium"),
						"Dep Date": st.column_config.TextColumn("📅 Dep", width="small"),
						"Ret Date": st.column_config.TextColumn("📅 Ret", width="small"),
						"Out €": st.column_config.TextColumn("✈️ Out", width="small"),
						"Back €": st.column_config.TextColumn("✈️ Back", width="small")
					}
				)
				
				# Show some quick stats
				col1, col2, col3 = st.columns(3)
				with col1:
					prices = [float(price.replace('€', '')) for price in summary_df['Price']]
					min_price = min(prices)
					best_duration = summary_df.loc[prices.index(min_price), 'Duration']
					st.metric("🏆 Best Deal", f"€{min_price:.0f}", f"{best_duration}")
				with col2:
					max_price = max(prices)
					st.metric("� Most Expensive", f"€{max_price:.0f}")
				with col3:
					price_diff = max_price - min_price
					st.metric("📈 Price Difference", f"€{price_diff:.0f}")
			else:
				st.warning("No flights found for 9, 10, or 11 day durations.")
		else:
			st.warning("No flights found for 9, 10, or 11 day durations.")
	else:
		st.warning("Missing required columns for price analysis.")

	# Now create filtered CSV files for tabs (keeping original logic for detailed view)
	filtered_csv_files = {}
	original_filenames = {}
	
	# For tabs, we'll group by original route combinations
	for df in all_flight_data:
		if not df.empty:
			source_file = df['source_file'].iloc[0]
			original_filename = df['original_filename'].iloc[0]
			
			# Remove the added columns for tab display
			tab_df = df.drop(['dep_from_airport', 'dep_to_airport', 'source_file', 'original_filename'], axis=1, errors='ignore')
			filtered_csv_files[source_file] = tab_df
			original_filenames[source_file] = original_filename

	# Sort tabs by departure date (ascending) - using already found original filenames
	sorted_tab_names = sorted(filtered_csv_files.keys(), key=lambda name: extract_departure_date(original_filenames.get(name, name)))

	# Create tabs for each file in sorted order
	tab_names = sorted_tab_names
	tabs = st.tabs(tab_names)

	for i, filename in enumerate(sorted_tab_names):
		df = filtered_csv_files[filename]
		with tabs[i]:
			st.header(f'📊 {filename}')

			if df.empty:
				st.warning('This file contains no data.')
				continue

			# Display basic info
			col1, col2, col3 = st.columns(3)
			with col1:
				st.metric('Total Combinations', len(df))

			if 'total_price' in df.columns:
				with col2:
					min_price = df['total_price'].min()
					st.metric('Cheapest', f'€{min_price:.2f}')
				with col3:
					avg_price = df['total_price'].mean()
					st.metric('Average Price', f'€{avg_price:.2f}')

			# Filtering options
			st.subheader('🔍 Filters')

			filter_col1, filter_col2, filter_col3 = st.columns(3)

			# Initialize filter ranges
			price_range = None
			duration_range = None
			selected_companies = []

			# Price filter
			if 'total_price' in df.columns:
				with filter_col1:
					min_price = float(df['total_price'].min())
					max_price = float(df['total_price'].max())

					# Handle case where min equals max
					if min_price == max_price:
						st.write(f'Price: €{min_price:.2f}')
						price_range = (min_price, max_price)
					else:
						price_range = st.slider('Price Range (€)', min_value=min_price, max_value=max_price, value=(min_price, max_price), key=f'price_{i}')

			# Duration filter
			if 'trip_duration_days' in df.columns:
				with filter_col2:
					min_duration = int(df['trip_duration_days'].min())
					max_duration = int(df['trip_duration_days'].max())

					# Handle case where min equals max
					if min_duration == max_duration:
						st.write(f'Trip Duration: {min_duration} days')
						duration_range = (min_duration, max_duration)
					else:
						duration_range = st.slider('Trip Duration (days)', min_value=min_duration, max_value=max_duration, value=(min_duration, max_duration), key=f'duration_{i}')

			# Company filter
			if 'dep_companies' in df.columns:
				with filter_col3:
					all_companies = set()
					for companies in df['dep_companies'].dropna():
						all_companies.update([c.strip() for c in str(companies).split(',')])

					selected_companies = st.multiselect('Airlines', options=sorted(all_companies), key=f'companies_{i}')

			# Apply filters
			filtered_df = df.copy()

			if 'total_price' in df.columns and price_range is not None:
				filtered_df = filtered_df[(filtered_df['total_price'] >= price_range[0]) & (filtered_df['total_price'] <= price_range[1])]

			if 'trip_duration_days' in df.columns and duration_range is not None:
				filtered_df = filtered_df[(filtered_df['trip_duration_days'] >= duration_range[0]) & (filtered_df['trip_duration_days'] <= duration_range[1])]

			if 'dep_companies' in df.columns and selected_companies:
				mask = filtered_df['dep_companies'].apply(lambda x: any(company in str(x) for company in selected_companies) if pd.notna(x) else False)
				filtered_df = filtered_df[mask]

			# Display filtered count
			if len(filtered_df) != len(df):
				st.info(f'Showing {len(filtered_df)} of {len(df)} combinations after filtering')

			# Sort options
			st.subheader('📈 Sorting')
			sort_col1, sort_col2 = st.columns(2)

			with sort_col1:
				sort_column = st.selectbox(
					'Sort by', options=filtered_df.columns.tolist(), index=0 if 'total_price' not in filtered_df.columns else filtered_df.columns.tolist().index('total_price'), key=f'sort_col_{i}'
				)

			with sort_col2:
				sort_order = st.selectbox('Order', options=['Ascending', 'Descending'], key=f'sort_order_{i}')

			# Apply sorting
			ascending = sort_order == 'Ascending'
			display_df = filtered_df.sort_values(by=sort_column, ascending=ascending)

			# Display flight combinations as cards
			st.subheader('✈️ Flight Combinations')

			if len(display_df) == 0:
				st.info('No flights match your filters.')
			else:
				# Add pagination for better performance
				items_per_page = 5
				total_items = len(display_df)
				total_pages = (total_items - 1) // items_per_page + 1

				if total_pages > 1:
					page = st.selectbox(f'Page (showing {items_per_page} flights per page)', range(1, total_pages + 1), key=f'page_{i}')
					start_idx = (page - 1) * items_per_page
					end_idx = min(start_idx + items_per_page, total_items)
					page_df = display_df.iloc[start_idx:end_idx]
					st.info(f'Showing flights {start_idx + 1}-{end_idx} of {total_items}')
				else:
					page_df = display_df
					st.info(f'Showing all {total_items} flights')

				for _idx, row in page_df.iterrows():
					# Format durations properly
					dep_duration = format_duration(row.get('dep_total_hours', 0))
					arr_duration = format_duration(row.get('arr_total_hours', 0))

					# Format flight details
					dep_date = pd.to_datetime(row.get('dep_departure_date', '')).strftime('%b %d') if pd.notna(row.get('dep_departure_date')) else 'N/A'
					dep_time = f'{row.get("dep_departure_time", "N/A")} - {row.get("dep_arrival_time", "N/A")}'
					dep_airline = row.get('dep_companies', 'N/A')
					if len(str(dep_airline)) > 20:
						dep_airline = str(dep_airline)[:20] + '...'
					dep_price = row.get('dep_price', 0)

					arr_date = pd.to_datetime(row.get('arr_departure_date', '')).strftime('%b %d') if pd.notna(row.get('arr_departure_date')) else 'N/A'
					arr_time = f'{row.get("arr_departure_time", "N/A")} - {row.get("arr_arrival_time", "N/A")}'
					arr_airline = row.get('arr_companies', 'N/A')
					if len(str(arr_airline)) > 20:
						arr_airline = str(arr_airline)[:20] + '...'
					arr_price = row.get('arr_price', 0)

					# Create a simple, clean flight card

					# Start card container
					st.markdown(
						"""
                    <div style="
                        border: 2px solid #ddd;
                        border-radius: 10px;
                        margin: 20px 0;
                        background: white;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                        padding: 20px;
                    ">
                    """,
						unsafe_allow_html=True,
					)

					# Header section with route and price - simple layout
					col_route, col_days, col_price = st.columns([2, 1, 1])

					with col_route:
						st.markdown(f'**✈️ {row.get("dep_departure_airport", "N/A")} → {row.get("dep_arrival_airport", "N/A")}**')

					with col_days:
						st.markdown(f'📅 **{row.get("trip_duration_days", "N/A")} days**')

					with col_price:
						st.markdown(f"<div style='text-align: right; font-size: 24px; font-weight: bold; color: #2e7d32;'>€{row.get('total_price', 0):.0f}</div>", unsafe_allow_html=True)

					st.markdown('---')

					# Flight details using streamlit columns
					col1, col2 = st.columns(2)

					# Outbound flight
					with col1:
						st.markdown(
							f"""
                        <div style="
                            background: #f5f5f5;
                            border: 1px solid #e0e0e0;
                            padding: 20px;
                            border-radius: 8px;
                            margin-bottom: 10px;
                        ">
                            <div style="
                                font-size: 18px;
                                font-weight: bold;
                                text-align: center;
                                margin-bottom: 15px;
                                color: #333;
                                border-bottom: 1px solid #ddd;
                                padding-bottom: 10px;
                            ">
                                🛫 OUTBOUND
                            </div>
                            <div style="
                                padding: 15px;
                                background: white;
                                border-radius: 5px;
                                margin-bottom: 15px;
                            ">
                                <div style="font-size: 14px; line-height: 1.8; color: #555;">
                                    <div><strong>📅 Date:</strong> {dep_date}</div>
                                    <div><strong>🕐 Time:</strong> {dep_time}</div>
                                    <div><strong>✈️ Airline:</strong> {dep_airline}</div>
                                    <div><strong>⏱️ Duration:</strong> {dep_duration}</div>
                                </div>
                            </div>
                            <div style="
                                text-align: center;
                                font-size: 20px;
                                font-weight: bold;
                                color: #2e7d32;
                                background: white;
                                padding: 10px;
                                border-radius: 5px;
                                border: 1px solid #e0e0e0;
                            ">
                                €{dep_price:.0f}
                            </div>
                        </div>
                        """,
							unsafe_allow_html=True,
						)

					# Return flight
					with col2:
						st.markdown(
							f"""
                        <div style="
                            background: #f5f5f5;
                            border: 1px solid #e0e0e0;
                            padding: 20px;
                            border-radius: 8px;
                            margin-bottom: 10px;
                        ">
                            <div style="
                                font-size: 18px;
                                font-weight: bold;
                                text-align: center;
                                margin-bottom: 15px;
                                color: #333;
                                border-bottom: 1px solid #ddd;
                                padding-bottom: 10px;
                            ">
                                🛬 RETURN
                            </div>
                            <div style="
                                padding: 15px;
                                background: white;
                                border-radius: 5px;
                                margin-bottom: 15px;
                            ">
                                <div style="font-size: 14px; line-height: 1.8; color: #555;">
                                    <div><strong>📅 Date:</strong> {arr_date}</div>
                                    <div><strong>🕐 Time:</strong> {arr_time}</div>
                                    <div><strong>✈️ Airline:</strong> {arr_airline}</div>
                                    <div><strong>⏱️ Duration:</strong> {arr_duration}</div>
                                </div>
                            </div>
                            <div style="
                                text-align: center;
                                font-size: 20px;
                                font-weight: bold;
                                color: #2e7d32;
                                background: white;
                                padding: 10px;
                                border-radius: 5px;
                                border: 1px solid #e0e0e0;
                            ">
                                €{arr_price:.0f}
                            </div>
                        </div>
                        """,
							unsafe_allow_html=True,
						)

					# Close card container
					st.markdown('</div>', unsafe_allow_html=True)

			# Download option
			csv_data = filtered_df.to_csv(index=False)
			safe_filename = filename.replace(' ', '_').replace('→', 'to').replace('(', '').replace(')', '').replace(' - ', '_')
			st.download_button(label='📥 Download filtered data', data=csv_data, file_name=f'filtered_{safe_filename}.csv', mime='text/csv', key=f'download_{i}')


if __name__ == '__main__':
	main()
