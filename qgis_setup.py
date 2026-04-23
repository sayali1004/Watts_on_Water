"""
QGIS Auto-Configuration Script for SCEIN Supabase Data
Run this in QGIS Python Console after setting up connection
"""

from qgis.core import (
    QgsDataSourceUri,
    QgsVectorLayer,
    QgsProject,
    QgsCategorizedSymbolRenderer,
    QgsSymbol,
    QgsRendererCategory,
    QgsSimpleFillSymbolLayer,
    QgsGraduatedSymbolRenderer,
    QgsStyle
)
from qgis.PyQt.QtCore import QTimer, QDateTime, QVariant
from qgis.PyQt.QtGui import QColor

# ============================================
# CONFIGURATION
# ============================================
SUPABASE_CONNECTION_NAME = "SCEIN Supabase"  # Must match your PostGIS connection name

# ============================================
# LAYER MANAGEMENT
# ============================================

def add_permits_layer():
    """Add main permits_data layer with styling"""
    uri = QgsDataSourceUri()
    
    # Get connection details from existing connection
    md = QgsProviderRegistry.instance().providerMetadata('postgres')
    conn = md.findConnection(SUPABASE_CONNECTION_NAME)
    
    if not conn:
        print(f"❌ Connection '{SUPABASE_CONNECTION_NAME}' not found!")
        print("Available connections:", md.connections().keys())
        return None
    
    # Build URI from connection
    uri_str = conn.uri()
    uri.setConnection(
        conn.configuration()['host'],
        conn.configuration()['port'],
        conn.configuration()['database'],
        conn.configuration()['username'],
        conn.configuration()['password']
    )
    
    # Set table (non-spatial for now)
    uri.setDataSource("public", "permits_data", None, "", "id")
    
    # Create layer
    layer = QgsVectorLayer(uri.uri(), "SCEIN Permits Data", "postgres")
    
    if not layer.isValid():
        print("❌ Failed to load layer!")
        return None
    
    # Add to project
    QgsProject.instance().addMapLayer(layer)
    
    # Apply styling
    style_by_type(layer)
    
    print(f"✓ Added layer: {layer.featureCount()} records")
    return layer


def style_by_type(layer):
    """Apply categorical styling by data_type"""
    
    # Define categories
    categories = []
    
    # Permit - Blue
    symbol = QgsSymbol.defaultSymbol(layer.geometryType())
    symbol.setColor(QColor('#2196F3'))
    category = QgsRendererCategory('permit', symbol, 'Permit')
    categories.append(category)
    
    # Incentive - Green
    symbol = QgsSymbol.defaultSymbol(layer.geometryType())
    symbol.setColor(QColor('#4CAF50'))
    category = QgsRendererCategory('incentive', symbol, 'Incentive')
    categories.append(category)
    
    # Regulation - Orange
    symbol = QgsSymbol.defaultSymbol(layer.geometryType())
    symbol.setColor(QColor('#FF9800'))
    category = QgsRendererCategory('regulation', symbol, 'Regulation')
    categories.append(category)
    
    # Apply renderer
    renderer = QgsCategorizedSymbolRenderer('data_type', categories)
    layer.setRenderer(renderer)
    layer.triggerRepaint()
    
    print("✓ Applied styling by data_type")


def add_view_layers():
    """Add all useful views as separate layers"""
    views = [
        ('active_permits', 'Active Permits'),
        ('active_incentives', 'Active Incentives'),
        ('active_regulations', 'Active Regulations'),
        ('california_county_stats', 'CA County Stats')
    ]
    
    md = QgsProviderRegistry.instance().providerMetadata('postgres')
    conn = md.findConnection(SUPABASE_CONNECTION_NAME)
    
    if not conn:
        print(f"❌ Connection '{SUPABASE_CONNECTION_NAME}' not found!")
        return
    
    added_layers = []
    
    for view_name, display_name in views:
        uri = QgsDataSourceUri()
        uri.setConnection(
            conn.configuration()['host'],
            conn.configuration()['port'],
            conn.configuration()['database'],
            conn.configuration()['username'],
            conn.configuration()['password']
        )
        
        # Determine primary key
        pk = 'id' if view_name != 'california_county_stats' else 'county'
        
        uri.setDataSource("public", view_name, None, "", pk)
        
        layer = QgsVectorLayer(uri.uri(), display_name, "postgres")
        
        if layer.isValid():
            QgsProject.instance().addMapLayer(layer)
            added_layers.append(display_name)
            print(f"✓ Added: {display_name} ({layer.featureCount()} records)")
        else:
            print(f"✗ Failed to load: {display_name}")
    
    return added_layers


# ============================================
# AUTO-REFRESH FUNCTIONALITY
# ============================================

def setup_auto_refresh(interval_minutes=5):
    """
    Set up automatic layer refresh
    
    Args:
        interval_minutes: Refresh interval in minutes
    """
    
    def refresh_all_layers():
        refreshed = []
        for layer_id, layer in QgsProject.instance().mapLayers().items():
            if layer.dataProvider().name() == 'postgres':
                layer.reload()
                refreshed.append(layer.name())
        
        iface.mapCanvas().refresh()
        timestamp = QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')
        print(f"✓ [{timestamp}] Refreshed {len(refreshed)} layers")
    
    # Create timer
    timer = QTimer()
    timer.timeout.connect(refresh_all_layers)
    timer.start(interval_minutes * 60 * 1000)  # Convert to milliseconds
    
    # Store timer reference to prevent garbage collection
    if not hasattr(iface, 'scein_refresh_timer'):
        iface.scein_refresh_timer = timer
    
    print(f"✓ Auto-refresh enabled: every {interval_minutes} minutes")
    print("To disable: iface.scein_refresh_timer.stop()")
    
    return timer


def stop_auto_refresh():
    """Stop auto-refresh timer"""
    if hasattr(iface, 'scein_refresh_timer'):
        iface.scein_refresh_timer.stop()
        print("✓ Auto-refresh stopped")
    else:
        print("No active refresh timer found")


# ============================================
# DATA ANALYSIS HELPERS
# ============================================

def get_county_summary(county_name):
    """Get summary statistics for a specific county"""
    layer = QgsProject.instance().mapLayersByName('SCEIN Permits Data')
    
    if not layer:
        print("❌ Layer 'SCEIN Permits Data' not found")
        return
    
    layer = layer[0]
    
    # Build filter
    layer.setSubsetString(f"county = '{county_name}'")
    
    # Get counts by type
    summary = {}
    for feature in layer.getFeatures():
        data_type = feature['data_type']
        status = feature['status']
        
        key = f"{data_type}_{status}"
        summary[key] = summary.get(key, 0) + 1
    
    # Clear filter
    layer.setSubsetString("")
    
    print(f"\n📊 Summary for {county_name}:")
    for key, count in sorted(summary.items()):
        print(f"  {key}: {count}")
    
    return summary


def search_permits(search_text):
    """Search permits by text"""
    layer = QgsProject.instance().mapLayersByName('SCEIN Permits Data')
    
    if not layer:
        print("❌ Layer not found")
        return
    
    layer = layer[0]
    
    # Build filter (case-insensitive search)
    filter_expr = f"""
        "parameter_name" ILIKE '%{search_text}%' OR
        "description" ILIKE '%{search_text}%' OR
        "requirements" ILIKE '%{search_text}%'
    """
    
    layer.setSubsetString(filter_expr)
    count = layer.featureCount()
    
    print(f"✓ Found {count} records matching '{search_text}'")
    print("To clear filter: layer.setSubsetString('')")
    
    return count


# ============================================
# QUICK SETUP FUNCTION
# ============================================

def quick_setup():
    """One-command setup: add layers and enable auto-refresh"""
    print("=" * 60)
    print("SCEIN QGIS Quick Setup")
    print("=" * 60)
    
    # Add main layer
    main_layer = add_permits_layer()
    
    if not main_layer:
        print("❌ Setup failed - check connection settings")
        return False
    
    # Add view layers
    print("\nAdding view layers...")
    add_view_layers()
    
    # Set up auto-refresh
    print("\nSetting up auto-refresh...")
    setup_auto_refresh(interval_minutes=5)
    
    # Zoom to layer extent
    if main_layer.featureCount() > 0:
        iface.setActiveLayer(main_layer)
        iface.zoomToActiveLayer()
    
    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)
    print("\n📋 Available functions:")
    print("  - get_county_summary('Alameda')")
    print("  - search_permits('solar')")
    print("  - stop_auto_refresh()")
    print("  - setup_auto_refresh(10)  # 10 minute interval")
    print("=" * 60)
    
    return True


# ============================================
# EXECUTION
# ============================================

# Uncomment to run setup automatically when this script loads:
# quick_setup()

print("✓ SCEIN QGIS functions loaded")
print("Run: quick_setup() to configure everything")
