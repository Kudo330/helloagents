export interface Location {
  longitude: number
  latitude: number
}

export interface Attraction {
  name: string
  address: string
  location: Location
  visit_duration: number
  description: string
  category?: string
  rating?: number
  image_url?: string
  ticket_price?: number
}

export interface Meal {
  type: 'breakfast' | 'lunch' | 'dinner' | 'snack'
  name: string
  address?: string
  location?: Location
  description?: string
  estimated_cost?: number
}

export interface Hotel {
  name: string
  address: string
  location?: Location
  price_range?: string
  rating?: string
  distance?: string
  type?: string
  estimated_cost?: number
}

export interface Budget {
  total_attractions?: number
  total_hotels?: number
  total_meals?: number
  total_transportation?: number
  total?: number
}

export interface WeatherInfo {
  date: string
  day_weather: string
  night_weather: string
  day_temp: number
  night_temp: number
  wind_direction: string
  wind_power: string
}

export interface DayPlan {
  date: string
  day_index: number
  description: string
  transportation: string
  accommodation: string
  hotel?: Hotel
  attractions: Attraction[]
  meals: Meal[]
  transport_legs: TransportLeg[]
}

export interface TransportLeg {
  mode: string
  from_name: string
  to_name: string
  distance_meters: number
  duration_minutes: number
  estimated_cost?: number
  summary: string
}

export interface TripPlan {
  city: string
  start_date: string
  end_date: string
  pace_preference: string
  safety_preference: string
  night_preference: string
  solo_reminders: string[]
  days: DayPlan[]
  weather_info: WeatherInfo[]
  overall_suggestions: string
  budget?: Budget
  success?: boolean
  fallback?: boolean
  partial_fallback?: boolean
}

export interface TripPlanRequest {
  city: string
  start_date: string
  end_date: string
  days: number
  preferences: string
  budget: string
  transportation: string
  accommodation: string
  pace_preference: string
  safety_preference: string
  night_preference: string
}
