import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  SafeAreaView,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
  StatusBar,
  RefreshControl,
  Alert
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Ionicons from '@expo/vector-icons/Ionicons';

const API_URL = 'http://localhost:5000/api/v1'; // Local network URL

export default function App() {
  const [scanStatus, setScanStatus] = useState('idle');
  const [diskUsage, setDiskUsage] = useState({ used_gb: 0, free_gb: 0, percent: 0 });
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [themeMode, setThemeMode] = useState('light');
  const [cleanupHistory, setCleanupHistory] = useState([]);

  useEffect(() => {
    loadCleanupHistory();
    fetchUsageStats();
  }, []);

  const loadCleanupHistory = async () => {
    try {
      const data = await AsyncStorage.getItem('cleanup_history');
      if (data) {
        setCleanupHistory(JSON.parse(data));
      }
    } catch (error) {
      console.log('Error loading history:', error);
    }
  };

  const fetchUsageStats = async () => {
    try {
      const response = await fetch(`${API_URL}/usage/stats`);
      const data = await response.json();
      setDiskUsage(data);
    } catch (error) {
      console.log('API Error:', error);
    }
  };

  const startScan = async () => {
    try {
      setScanStatus('scanning');
      const response = await fetch(`${API_URL}/scan/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ drive: 'C:' })
      });
      
      const result = await response.json();
      
      setTimeout(() => {
        fetchUsageStats();
        setScanStatus('complete');
        showNotification('Scan Complete!');
      }, 5000);
    } catch (error) {
      console.log('Scan Error:', error);
      setScanStatus('idle');
    }
  };

  const runSmartCleanup = async () => {
    try {
      Alert.alert(
        'Confirm Cleanup',
        'This will automatically clean temporary files and duplicates. Continue?',
        [
          { text: 'Cancel', style: 'cancel' },
          { 
            text: 'Clean', 
            onPress: async () => {
              const cleanupStartTime = Date.now();
              
              const response = await fetch(`${API_URL}/cleanup/run`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type: 'smart' })
              });
              
              const result = await response.json();
              
              if (result.status === 'success') {
                const freed_mb = result.space_freed_mb;
                
                // Save to history
                const newEntry = {
                  date: new Date().toISOString(),
                  freed_mb: freed_mb,
                  saved_kb: freed_mb * 1024
                };
                
                const newHistory = [newEntry, ...cleanupHistory];
                setCleanupHistory(newHistory);
                
                try {
                  await AsyncStorage.setItem('cleanup_history', JSON.stringify(newHistory));
                } catch (e) {}
                
                fetchUsageStats();
                showNotification(`Successfully freed ${freed_mb.toFixed(2)} MB!`);
              }
            }
          }
        ]
      );
    } catch (error) {
      Alert.alert('Error', 'Could not perform cleanup. Try again.');
    }
  };

  const showNotification = (message) => {
    Alert.alert('EatUp Pro', message, [{ text: 'OK' }]);
  };

  const toggleTheme = () => {
    const newTheme = themeMode === 'light' ? 'dark' : 'light';
    setThemeMode(newTheme);
    saveThemePreference(newTheme);
  };

  const saveThemePreference = async (theme) => {
    try {
      await AsyncStorage.setItem('theme_preference', theme);
    } catch (error) {}
  };

  const renderDiskUsage = () => {
    const percentage = diskUsage.percent || 0;
    let color = '#10b981'; // green
    if (percentage > 70) color = '#f59e0b'; // yellow
    if (percentage > 90) color = '#ef4444'; // red

    return (
      <View style={styles.diskContainer}>
        <Text style={[styles.sectionTitle, { color: getTextColor() }]}>Storage Usage</Text>
        
        {/* Circular Progress */}
        <View style={styles.circleContainer}>
          <View style={[styles.circleOutline, { borderWidth: 12 }]}>
            <View style={[styles.circleFill, {
              width: '100%',
              height: '100%',
              borderRadius: 60,
              transform: [{ rotate: '-90deg' }],
              opacity: 0.3
            }]} />
            <View style={[styles.circleProgress, {
              width: '100%',
              height: '100%',
              borderRadius: 60,
              transform: [{ rotate: '-90deg' }],
              borderTopWidth: 12,
              borderRightWidth: 12,
              borderBottomWidth: 12,
              borderLeftWidth: 12,
              borderColor: `${color} ${getFillColor()} transparent transparent transparent`,
              borderImageSource: null
            }]} />
          </View>
          <View style={styles.circleText}>
            <Text style={[styles.largeNumber, { color: getColorPrimary() }]}>
              {percentage.toFixed(1)}%
            </Text>
            <Text style={[styles.statusText, { color: getSecondaryColor() }]}>Used</Text>
          </View>
        </View>

        <View style={styles.statsRow}>
          <View style={styles.statItem}>
            <Text style={[styles.statLabel, { color: getTextColor() }]}>Used</Text>
            <Text style={[styles.statValue, { color: getColorPrimary() }]}>
              {diskUsage.used_gb?.toFixed(1) || 0} GB
            </Text>
          </View>
          <View style={styles.statItem}>
            <Text style={[styles.statLabel, { color: getTextColor() }]}>Free</Text>
            <Text style={[styles.statValue, { color: getColorSuccess() }]}>
              {diskUsage.free_gb?.toFixed(1) || 0} GB
            </Text>
          </View>
        </View>
      </View>
    );
  };

  const renderQuickActions = () => {
    return (
      <View style={styles.actionsSection}>
        <Text style={[styles.sectionTitle, { color: getTextColor() }]}>Quick Actions</Text>
        <View style={styles.actionsGrid}>
          <TouchableOpacity 
            style={[styles.actionButton, styles.scanButton]}
            onPress={startScan}
            disabled={scanStatus === 'scanning'}
          >
            {scanStatus === 'scanning' ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Ionicons name="scan-outline" size={32} color="#fff" />
            )}
            <Text style={styles.actionButtonText}>Quick Scan</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.actionButton, styles.cleanupButton]}
            onPress={runSmartCleanup}
          >
            <Ionicons name="trash-outline" size={32} color="#fff" />
            <Text style={styles.actionButtonText}>Smart Clean</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.actionButton, styles.scheduleButton]}
            onPress={() => {}}
          >
            <Ionicons name="calendar-outline" size={32} color="#fff" />
            <Text style={styles.actionButtonText}>Schedule</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.actionButton, styles.cloudButton]}
            onPress={() => {}}
          >
            <Ionicons name="cloud-outline" size={32} color="#fff" />
            <Text style={styles.actionButtonText}>Cloud Sync</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  const renderCleanupHistory = () => {
    const historyItems = cleanupHistory.slice(0, 5);
    
    return (
      <View style={styles.historySection}>
        <Text style={[styles.sectionTitle, { color: getTextColor() }]}>Recent Cleans</Text>
        <FlatList
          data={historyItems}
          keyExtractor={(item, index) => index.toString()}
          renderItem={({ item }) => (
            <View style={[styles.historyItem, { backgroundColor: getCardBackground() }]}>
              <View style={styles.historyIcon}>
                <Ionicons name="checkmark-circle" size={24} color="#10b981" />
              </View>
              <View style={styles.historyContent}>
                <Text style={styles.historyDate}>
                  {new Date(item.date).toLocaleDateString()} at {new Date(item.date).toLocaleTimeString()}
                </Text>
                <Text style={[styles.historySaved, { color: getColorSuccess() }]}>
                  Saved {item.saved_kb?.toFixed(0)?.toLocaleString()} KB
                </Text>
              </View>
            </View>
          )}
          ListEmptyComponent={
            <View style={styles.emptyState}>
              <Ionicons name="time-outline" size={48} color="#ccc" />
              <Text style={{ color: '#999' }}>No cleanup history yet</Text>
            </View>
          }
        />
      </View>
    );
  };

  const getBackgroundColor = () => themeMode === 'dark' ? '#1a1a1a' : '#ffffff';
  const getCardBackground = () => themeMode === 'dark' ? '#2d2d2d' : '#f9fafb';
  const getTextColor = () => themeMode === 'dark' ? '#ffffff' : '#1f2937';
  const getColorPrimary = () => themeMode === 'dark' ? '#60a5fa' : '#3b82f6';
  const getColorSuccess = () => '#10b981';
  const getSecondaryColor = () => themeMode === 'dark' ? '#9ca3af' : '#6b7280';
  
  const stylesApp = StyleSheet.create({
    container: { flex: 1, backgroundColor: getBackgroundColor() },
    header: { padding: 16, backgroundColor: getCardBackground() },
    headerTitle: { fontSize: 24, fontWeight: 'bold', color: getColorPrimary() },
    sectionTitle: { fontSize: 18, fontWeight: '600', marginBottom: 12 },
    actionsSection: { padding: 16 },
    actionsGrid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' },
    actionButton: {
      width: '48%',
      marginVertical: 8,
      padding: 20,
      borderRadius: 12,
      alignItems: 'center'
    },
    scanButton: { backgroundColor: '#3b82f6' },
    cleanupButton: { backgroundColor: '#10b981' },
    scheduleButton: { backgroundColor: '#8b5cf6' },
    cloudButton: { backgroundColor: '#ec4899' },
    actionButtonText: { color: '#ffffff', marginTop: 8, fontWeight: '600' },
    historySection: { padding: 16 },
    historyItem: {
      flexDirection: 'row',
      padding: 16,
      borderRadius: 8,
      marginBottom: 8,
      backgroundColor: '#f9fafb'
    },
    historyIcon: { marginRight: 12 },
    historyContent: { flex: 1 },
    historyDate: { fontSize: 14, color: '#6b7280' },
    historySaved: { fontSize: 16, fontWeight: '600' },
    emptyState: { padding: 32, alignItems: 'center', opacity: 0.5 },
    largeNumber: { fontSize: 32, fontWeight: 'bold' },
    statusText: { fontSize: 14, marginTop: 4 },
    statsRow: { flexDirection: 'row', justifyContent: 'space-around', marginTop: 16 },
    statItem: { alignItems: 'center' },
    statLabel: { fontSize: 12, opacity: 0.7, marginBottom: 4 },
    statValue: { fontSize: 16, fontWeight: '600' },
    circleContainer: { position: 'relative', width: 150, height: 150, alignItems: 'center' },
    circleOutline: {
      width: 120,
      height: 120,
      borderRadius: 60,
      position: 'absolute'
    },
    circleText: { position: 'absolute', top: 35 },
    themeToggle: {
      position: 'absolute',
      right: 16,
      top: 24,
      width: 40,
      height: 40,
      borderRadius: 20,
      backgroundColor: '#f3f4f6',
      justifyContent: 'center',
      alignItems: 'center'
    },
    toolbar: { flexDirection: 'row', paddingHorizontal: 16, paddingVertical: 12, backgroundColor: getCardBackground() },
    toolbarItem: { flex: 1, alignItems: 'center', paddingVertical: 8 },
    toolbarIcon: { fontSize: 24 },
    toolbarLabel: { fontSize: 12, marginTop: 4 }
  });

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle={themeMode === 'dark' ? 'light-content' : 'dark-content'} />
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>EatUp Pro</Text>
        <TouchableOpacity style={styles.themeToggle} onPress={toggleTheme}>
          <Ionicons 
            name={themeMode === 'dark' ? 'sunny-outline' : 'moon-outline'} 
            size={24} 
            color={getColorPrimary()} 
          />
        </TouchableOpacity>
      </View>

      <ScrollView 
        refreshControl={
          <RefreshControl refreshing={isRefreshing} onRefresh={fetchUsageStats} />
        }
      >
        {renderDiskUsage()}
        {renderQuickActions()}
        {renderCleanupHistory()}
      </ScrollView>
    </SafeAreaView>
  );
}
