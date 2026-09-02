export interface MarineRegion {
  id: string;
  name: string;
  category: 'Indian Ocean System' | 'Global Oceans' | 'Regional Seas';
  lat: number;
  lon: number;
  height: number;
  pitch: number; // degrees
  heading: number; // degrees
  description: string;
}

export const MARINE_REGIONS: MarineRegion[] = [
  {
    id: 'global-orbit',
    name: '🌐 Full Earth Orbit View',
    category: 'Global Oceans',
    lat: 15.0,
    lon: 75.0,
    height: 18000000,
    pitch: -85,
    heading: 0,
    description: 'Full 3D spherical planetary view in space'
  },
  {
    id: 'indian-ocean',
    name: '🌊 Indian Ocean (Main Surface)',
    category: 'Indian Ocean System',
    lat: 0.0,
    lon: 78.0,
    height: 6500000,
    pitch: -75,
    heading: 0,
    description: 'Primary equatorial Indian Ocean surface domain'
  },
  {
    id: 'arabian-sea',
    name: '🌊 Arabian Sea',
    category: 'Indian Ocean System',
    lat: 15.0,
    lon: 64.5,
    height: 3500000,
    pitch: -75,
    heading: 0,
    description: 'North-Western Indian Ocean & high-salinity zone'
  },
  {
    id: 'bay-of-bengal',
    name: '🌊 Bay of Bengal',
    category: 'Indian Ocean System',
    lat: 14.5,
    lon: 88.5,
    height: 3500000,
    pitch: -75,
    heading: 0,
    description: 'North-Eastern Indian Ocean & freshwater runoff basin'
  },
  {
    id: 'laccadive-sea',
    name: '🌊 Laccadive / Lakshadweep Sea',
    category: 'Indian Ocean System',
    lat: 9.0,
    lon: 74.5,
    height: 2200000,
    pitch: -75,
    heading: 0,
    description: 'South-Western Indian coastal marine shelf'
  },
  {
    id: 'andaman-sea',
    name: '🌊 Andaman Sea',
    category: 'Indian Ocean System',
    lat: 10.5,
    lon: 95.0,
    height: 2500000,
    pitch: -75,
    heading: 0,
    description: 'Eastern sub-basin bordering Malay Peninsula'
  },
  {
    id: 'red-sea',
    name: '🌊 Red Sea & Gulf of Aden',
    category: 'Regional Seas',
    lat: 18.0,
    lon: 42.0,
    height: 2800000,
    pitch: -75,
    heading: 0,
    description: 'High salinity evaporative sea corridor'
  },
  {
    id: 'persian-gulf',
    name: '🌊 Persian Gulf',
    category: 'Regional Seas',
    lat: 26.5,
    lon: 52.5,
    height: 2000000,
    pitch: -75,
    heading: 0,
    description: 'Shallow semi-enclosed marginal sea'
  },
  {
    id: 'north-atlantic',
    name: '🌊 North Atlantic Ocean',
    category: 'Global Oceans',
    lat: 32.0,
    lon: -45.0,
    height: 6500000,
    pitch: -75,
    heading: 0,
    description: 'Gulf Stream & Subpolar Gyre system'
  },
  {
    id: 'south-pacific',
    name: '🌊 South Pacific Ocean',
    category: 'Global Oceans',
    lat: -20.0,
    lon: -140.0,
    height: 7500000,
    pitch: -75,
    heading: 0,
    description: 'Humboldt Current & Equatorial Gyre'
  }
];
