import folium

mymap=folium.Map([48.858844, 2.294350], zoom_start=15)
folium.Marker([48.858844, 2.294350], tooltip="부단대학교", icon=folium.Icon(color="red", icon="univercity", prefix="fa" )
).add_to(mymap)

mymap.show_in_browser()