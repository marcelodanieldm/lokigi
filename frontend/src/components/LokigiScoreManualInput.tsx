"use client"

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, ClipboardPaste, TrendingUp, TrendingDown, DollarSign, MapPin, Star, Image, Tag, CheckCircle } from 'lucide-react'

interface LokigiScoreResult {
  total_score: number
  score_label: string
  dimension_scores: {
    NAP: number
    Reseñas: number
    Fotos: number
    Categorías: number
    Verificación: number
  }
  lucro_cesante_mensual_usd: number
  lucro_cesante_anual_usd: number
  clientes_perdidos_mes: number
  ranking_position_estimated: number
  ranking_improvement_potential: number
  critical_issues: string[]
  recommendations: string[]
  analyzed_at: string
  country: string
}

export default function LokigiScoreManualInput() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<LokigiScoreResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  
  const [formData, setFormData] = useState({
    business_name: '',
    address: '',
    phone: '',
    website: '',
    rating: '',
    reviews: '',
    claimed_text: '',
    verified_badge: false,
    primary_category: '',
    additional_categories: '',
    photo_count: '',
    last_photo_date: '',
    business_hours: '',
    country_code: 'AR',
    city: '',
    lead_email: ''
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    }))
  }

  const handleCountryChange = (value: string) => {
    setFormData(prev => ({ ...prev, country_code: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch('http://localhost:8000/api/lokigi-score/analyze-manual', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(formData)
      })

      if (!response.ok) {
        throw new Error('Error al analizar los datos')
      }

      const data: LokigiScoreResult = await response.json()
      setResult(data)
    } catch (err: any) {
      setError(err.message || 'Error al procesar la solicitud')
    } finally {
      setLoading(false)
    }
  }

  const getDimensionColor = (score: number) => {
    if (score >= 16) return 'text-green-600'
    if (score >= 12) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getScoreColor = (score: number) => {
    if (score >= 85) return 'text-green-600'
    if (score >= 70) return 'text-blue-600'
    if (score >= 50) return 'text-yellow-600'
    if (score >= 30) return 'text-orange-600'
    return 'text-red-600'
  }

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">🎯 Lokigi Score - Análisis Manual</h1>
        <p className="text-muted-foreground">
          Copia y pega los datos directamente desde Google Maps para calcular el score y lucro cesante.
          <br />
          <strong>Presupuesto cero - Sin APIs costosas</strong>
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* FORMULARIO */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ClipboardPaste className="w-5 h-5" />
                Datos del Negocio (Google Maps)
              </CardTitle>
              <CardDescription>
                Copia los datos directamente del perfil de Google Maps
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Información Básica */}
                <div className="space-y-2">
                  <Label htmlFor="business_name">Nombre del Negocio *</Label>
                  <Input
                    id="business_name"
                    name="business_name"
                    value={formData.business_name}
                    onChange={handleChange}
                    placeholder="Ej: Pizzería Don Juan"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="address">Dirección Completa *</Label>
                  <Input
                    id="address"
                    name="address"
                    value={formData.address}
                    onChange={handleChange}
                    placeholder="Ej: Av. Corrientes 1234, Buenos Aires"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="phone">Teléfono</Label>
                    <Input
                      id="phone"
                      name="phone"
                      value={formData.phone}
                      onChange={handleChange}
                      placeholder="+54 11 4444-5555"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="website">Sitio Web</Label>
                    <Input
                      id="website"
                      name="website"
                      value={formData.website}
                      onChange={handleChange}
                      placeholder="www.ejemplo.com"
                    />
                  </div>
                </div>

                {/* Métricas Visibles */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="rating">Rating *</Label>
                    <Input
                      id="rating"
                      name="rating"
                      value={formData.rating}
                      onChange={handleChange}
                      placeholder="4.5"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="reviews">Reseñas *</Label>
                    <Input
                      id="reviews"
                      name="reviews"
                      value={formData.reviews}
                      onChange={handleChange}
                      placeholder="230 reseñas"
                      required
                    />
                  </div>
                </div>

                {/* Estado del Negocio */}
                <div className="space-y-2">
                  <Label htmlFor="claimed_text">Texto de Reclamación</Label>
                  <Input
                    id="claimed_text"
                    name="claimed_text"
                    value={formData.claimed_text}
                    onChange={handleChange}
                    placeholder="Ej: 'Propietario de esta empresa' o vacío"
                  />
                  <p className="text-xs text-muted-foreground">
                    Copia el texto que indique si el negocio está reclamado
                  </p>
                </div>

                {/* Categorías */}
                <div className="space-y-2">
                  <Label htmlFor="primary_category">Categoría Principal *</Label>
                  <Input
                    id="primary_category"
                    name="primary_category"
                    value={formData.primary_category}
                    onChange={handleChange}
                    placeholder="Ej: Pizzería, Restaurante, Hotel"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="additional_categories">Categorías Adicionales</Label>
                  <Input
                    id="additional_categories"
                    name="additional_categories"
                    value={formData.additional_categories}
                    onChange={handleChange}
                    placeholder="Restaurante italiano, Delivery, Bar"
                  />
                  <p className="text-xs text-muted-foreground">
                    Separar con comas
                  </p>
                </div>

                {/* Fotos */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="photo_count">Cantidad de Fotos</Label>
                    <Input
                      id="photo_count"
                      name="photo_count"
                      value={formData.photo_count}
                      onChange={handleChange}
                      placeholder="45"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="last_photo_date">Última Foto</Label>
                    <Input
                      id="last_photo_date"
                      name="last_photo_date"
                      value={formData.last_photo_date}
                      onChange={handleChange}
                      placeholder="hace 2 semanas"
                    />
                  </div>
                </div>

                {/* Horarios */}
                <div className="space-y-2">
                  <Label htmlFor="business_hours">Horarios de Atención</Label>
                  <Textarea
                    id="business_hours"
                    name="business_hours"
                    value={formData.business_hours}
                    onChange={handleChange}
                    placeholder="Lun-Vie: 9:00-18:00"
                    rows={2}
                  />
                </div>

                {/* Ubicación */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="country_code">País *</Label>
                    <Select value={formData.country_code} onValueChange={handleCountryChange}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="AR">🇦🇷 Argentina</SelectItem>
                        <SelectItem value="BR">🇧🇷 Brasil</SelectItem>
                        <SelectItem value="US">🇺🇸 Estados Unidos</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="city">Ciudad</Label>
                    <Input
                      id="city"
                      name="city"
                      value={formData.city}
                      onChange={handleChange}
                      placeholder="Buenos Aires"
                    />
                  </div>
                </div>

                {/* Email del Lead (opcional) */}
                <div className="space-y-2">
                  <Label htmlFor="lead_email">Email del Lead (opcional)</Label>
                  <Input
                    id="lead_email"
                    name="lead_email"
                    type="email"
                    value={formData.lead_email}
                    onChange={handleChange}
                    placeholder="cliente@ejemplo.com"
                  />
                  <p className="text-xs text-muted-foreground">
                    Si existe un lead, el análisis se guardará automáticamente
                  </p>
                </div>

                <Button type="submit" className="w-full" disabled={loading}>
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Analizando...
                    </>
                  ) : (
                    <>
                      <TrendingUp className="w-4 h-4 mr-2" />
                      Calcular Lokigi Score
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* RESULTADOS */}
        <div className="space-y-6">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {result && (
            <>
              {/* Score Total */}
              <Card>
                <CardHeader>
                  <CardTitle>Lokigi Score Total</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center">
                    <div className={`text-6xl font-bold mb-2 ${getScoreColor(result.total_score)}`}>
                      {result.total_score}/100
                    </div>
                    <div className="text-xl font-semibold text-muted-foreground">
                      {result.score_label}
                    </div>
                  </div>

                  {/* Dimensiones */}
                  <div className="mt-6 space-y-3">
                    <h3 className="font-semibold mb-4">Score por Dimensión (20 pts c/u):</h3>
                    
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-2">
                        <MapPin className="w-4 h-4" />
                        NAP (Nombre, Dirección, Teléfono)
                      </span>
                      <span className={`font-bold ${getDimensionColor(result.dimension_scores.NAP)}`}>
                        {result.dimension_scores.NAP}/20
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-2">
                        <Star className="w-4 h-4" />
                        Reseñas
                      </span>
                      <span className={`font-bold ${getDimensionColor(result.dimension_scores.Reseñas)}`}>
                        {result.dimension_scores.Reseñas}/20
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-2">
                        <Image className="w-4 h-4" />
                        Fotos
                      </span>
                      <span className={`font-bold ${getDimensionColor(result.dimension_scores.Fotos)}`}>
                        {result.dimension_scores.Fotos}/20
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-2">
                        <Tag className="w-4 h-4" />
                        Categorías
                      </span>
                      <span className={`font-bold ${getDimensionColor(result.dimension_scores.Categorías)}`}>
                        {result.dimension_scores.Categorías}/20
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4" />
                        Verificación
                      </span>
                      <span className={`font-bold ${getDimensionColor(result.dimension_scores.Verificación)}`}>
                        {result.dimension_scores.Verificación}/20
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Lucro Cesante */}
              <Card className="border-red-200 bg-red-50">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-red-700">
                    <DollarSign className="w-5 h-5" />
                    💸 Lucro Cesante
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-red-700">
                      ${result.lucro_cesante_mensual_usd.toLocaleString()} USD/mes
                    </div>
                    <div className="text-lg text-muted-foreground">
                      (${result.lucro_cesante_anual_usd.toLocaleString()} USD/año)
                    </div>
                  </div>

                  <div className="bg-white rounded-lg p-4 space-y-2">
                    <div className="flex justify-between">
                      <span>Clientes perdidos por mes:</span>
                      <span className="font-bold">{result.clientes_perdidos_mes}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Posición estimada actual:</span>
                      <span className="font-bold">#{result.ranking_position_estimated}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Potencial de mejora:</span>
                      <span className="font-bold text-green-600">
                        ↑ {result.ranking_improvement_potential} posiciones
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Problemas Críticos */}
              {result.critical_issues.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-red-600">🚨 Problemas Críticos</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {result.critical_issues.map((issue, idx) => (
                        <li key={idx} className="text-sm bg-red-50 p-3 rounded border-l-4 border-red-500">
                          {issue}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}

              {/* Recomendaciones */}
              {result.recommendations.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-blue-600">✅ Plan de Acción</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {result.recommendations.map((rec, idx) => (
                        <li key={idx} className="text-sm bg-blue-50 p-3 rounded border-l-4 border-blue-500">
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
