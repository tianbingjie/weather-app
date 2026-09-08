# WeatherCN（华风爱科）标准版天气 API 完整整理

> **整理目标**：把 WeatherCN 开发文档中当前公开的“标准能力”接口集中整理到一个 Markdown 文件中，方便使用 Python `requests` 学习和后续开发天气 Web App。
>
> **官方文档总入口**：https://platform.weathercn.com/api-doc/overview
>
> **API 服务域名**：`https://openapi.weathercn.com`
>
> **整理日期**：2026-09-08
>
> **说明**：本文重点收录截图所示 API-DOC 中属于“标准能力”的接口；天文、台风、天气视频等目前官方文档标注为进阶/订阅能力，因此单独列在最后，不混入标准接口清单。

---

# 1. 标准版接口总览

根据当前 WeatherCN 开发文档，主要标准能力可以归纳为：

| 分类 | 标准接口 | 是否需要 Location Key |
|---|---|---:|
| 定位 | 城市文字搜索 | 否 |
| 定位 | 经纬度 GeoPosition | 否 |
| 实况 | 当前实况天气 | 是 |
| 预报 | 1/5/10 日预报 | 是 |
| 预报 | 1/12/24/72 小时预报 | 是 |
| 预报 | 中国分钟级降水 | 否 |
| 预警 | 当前气象预警 | 是 |
| 指数 | 1 日生活指数 | 是 |
| 空气质量 | 当前空气质量 | 是 |

核心调用关系：

```text
用户输入城市
      ↓
定位 API
      ↓
Location Key
      ↓
┌───────────────────────────────────┐
│ 实况 / 逐日 / 逐小时 / 预警       │
│ 生活指数 / 空气质量               │
└───────────────────────────────────┘

经纬度
  ↓
分钟级降水
```

官方当前文档同时说明：标准测试 Key 为 30 天试用、每日 500 次、5 QPS；实际配额和权限应以控制台当前显示为准。

---

# 2. 通用请求规范

## 2.1 API Key

常见请求参数：

```text
apikey=YOUR_API_KEY
```

推荐 Python：

```python
import os

API_KEY = os.getenv("WEATHER_API_KEY")

if not API_KEY:
    raise RuntimeError("WEATHER_API_KEY 未设置")
```

---

## 2.2 公共请求参数

多数 Location Key 类型接口：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---:|---|---|
| apikey | String | 是 | - | API 密钥 |
| version | String | 是 | v1 | API 版本 |
| locationkey | String | 是 | - | 地点唯一 ID |
| format | String | 否 | JSON | 返回格式 |
| language | String | 否 | en-us | 返回语言，如 `zh-cn` |
| details | String | 否 | false | 是否返回完整字段 |

部分预报接口额外支持：

```text
metric=true
```

表示使用公制单位。

---

## 2.3 requests 基础模板

```python
import requests

url = "https://openapi.weathercn.com/..."

params = {
    "apikey": "YOUR_API_KEY"
}

response = requests.get(
    url,
    params=params,
    timeout=10
)

response.raise_for_status()

data = response.json()

print(data)
```

建议：

```python
print(response.status_code)
print(response.url)
print(response.json())
```

学习时重点观察：

```text
response.status_code
response.text
response.json()
response.url
```

---

# 3. 定位搜索 API

## 3.1 作用

定位 API 是整个天气 API 的入口。

先通过：

```text
城市名称
```

或者：

```text
纬度 + 经度
```

获取：

```text
Location Key
```

然后再用 Location Key 调用天气接口。

官方文档当前说明支持全球 300 万+ 城市/区域搜索；GeoPosition 支持中国大陆 GCJ-02 与 WGS-84 坐标系。

---

## 3.2 标准接口一：城市文字搜索

### URL

```http
GET https://openapi.weathercn.com/locations/v1/cities/translate
```

### 示例

```text
https://openapi.weathercn.com/locations/v1/cities/translate?apikey=YOUR_API_KEY&q=北京&language=zh-cn&details=false
```

### 参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| apikey | String | 是 | API Key |
| q | String | 是 | 城市名、邮编等搜索文本 |
| language | String | 否 | 返回语言 |
| details | String | 否 | 是否返回完整位置数据 |
| offset | String | 否 | 结果偏移量 |
| alias | String | 否 | 别名匹配策略：`Never` / `Always` / `NoOfficialMatch` |

### Python

```python
import requests

url = "https://openapi.weathercn.com/locations/v1/cities/translate"

params = {
    "apikey": "YOUR_API_KEY",
    "q": "北京",
    "language": "zh-cn",
    "details": "true"
}

response = requests.get(
    url,
    params=params,
    timeout=10
)

response.raise_for_status()

data = response.json()

print(data)
```

---

## 3.3 文字搜索返回字段

### 顶层字段

| 字段 | 类型 | 说明 |
|---|---|---|
| Version | Int | 数据版本 |
| Key | String | Location Key |
| Type | String | 地点类型 |
| Rank | Int | 排名 |
| LocalizedName | String | 本地名称 |
| EnglishName | String | 英文名称 |
| PrimaryPostalCode | String | 主要邮政编码 |
| Region | Object | 区域 |
| Country | Object | 国家 |
| AdministrativeArea | Object | 行政区 |
| TimeZone | Object | 时区 |
| GeoPosition | Object | 经纬度、高程 |
| IsAlias | Boolean | 是否为别名 |
| SupplementalAdminAreas | Array | 补充行政区划 |
| DataSets | Array | 可用数据集 |

### Region

```text
Region.ID
Region.LocalizedName
Region.EnglishName
```

### Country

```text
Country.ID
Country.LocalizedName
Country.EnglishName
```

### AdministrativeArea

```text
AdministrativeArea.ID
AdministrativeArea.LocalizedName
AdministrativeArea.EnglishName
AdministrativeArea.Level
AdministrativeArea.LocalizedType
AdministrativeArea.EnglishType
AdministrativeArea.CountryID
```

### TimeZone

```text
TimeZone.Code
TimeZone.Name
TimeZone.GmtOffset
TimeZone.IsDaylightSaving
TimeZone.NextOffsetChange
```

### GeoPosition

```text
GeoPosition.Latitude
GeoPosition.Longitude
GeoPosition.Elevation
```

---

## 3.4 标准接口二：GeoPosition 经纬度查询

### URL

```http
GET https://openapi.weathercn.com/locations/v1/cities/geoposition/search.json
```

### 示例

```text
https://openapi.weathercn.com/locations/v1/cities/geoposition/search.json?apikey=YOUR_API_KEY&q=39.9,116.3&language=zh-cn
```

### 参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| apikey | String | 是 | API Key |
| q | String | 是 | `纬度,经度` |
| language | String | 否 | 返回语言 |

推荐：

```text
q=39.900,116.300
```

官方建议坐标保留约 3 位小数。

---

## 3.5 GeoPosition 返回字段

核心结构与城市搜索基本一致，另外可能出现：

```text
ParentCity
```

其常见字段：

```text
ParentCity.Key
ParentCity.LocalizedName
ParentCity.EnglishName
```

GeoPosition 示例：

```python
import requests

url = "https://openapi.weathercn.com/locations/v1/cities/geoposition/search.json"

params = {
    "apikey": "YOUR_API_KEY",
    "q": "39.9,116.3",
    "language": "zh-cn"
}

response = requests.get(url, params=params, timeout=10)

response.raise_for_status()

data = response.json()

print(data)
```

---

# 4. 实况天气 API

## 4.1 标准接口

```http
GET https://openapi.weathercn.com/currentconditions/v1/{locationkey}.json
```

北京示例：

```text
https://openapi.weathercn.com/currentconditions/v1/101924.json?apikey=YOUR_API_KEY&language=zh-cn&details=true
```

官方说明：默认返回简版数据；增加 `details=true` 获取完整实况字段。

---

## 4.2 请求参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| apikey | String | 是 | API Key |
| version | String | 是 | `v1` |
| locationkey | String | 是 | 地点 Key |
| format | String | 否 | 默认 JSON |
| language | String | 否 | 返回语言 |
| details | String | 否 | `true` 获取完整字段 |

---

## 4.3 Python

```python
import requests

location_key = "101924"

url = (
    "https://openapi.weathercn.com/"
    f"currentconditions/v1/"
    f"{location_key}.json"
)

params = {
    "apikey": "YOUR_API_KEY",
    "language": "zh-cn",
    "details": "true"
}

response = requests.get(
    url,
    params=params,
    timeout=10
)

response.raise_for_status()

data = response.json()

weather = data[0]

print("天气：", weather["WeatherText"])
print(
    "温度：",
    weather["Temperature"]["Metric"]["Value"],
    weather["Temperature"]["Metric"]["Unit"]
)
print("湿度：", weather["RelativeHumidity"])
```

---

## 4.4 实况返回字段

### 基础字段

| 字段 | 类型 | 说明 |
|---|---|---|
| LocalObservationDateTime | String | 本地观测时间 |
| EpochTime | Int | UNIX 时间戳 |
| WeatherIcon | Int | 天气图标编号 |
| WeatherText | String | 天气描述 |
| HasPrecipitation | Boolean | 是否有降水 |
| PrecipitationType | String | 降水类型 |
| IsDayTime | Boolean | 是否白天 |
| RelativeHumidity | Int | 相对湿度 |
| MobileLink | String | 移动端链接 |
| Link | String | 网页链接 |

### LocalSource

```text
LocalSource.Id
LocalSource.Name
LocalSource.WeatherCode
LocalSource.WindLevel
LocalSource.WindDirectionCode
LocalSource.WindGustDirectionCode
LocalSource.Temperature
```

### Temperature

```text
Temperature.Metric.Value
Temperature.Metric.Unit
Temperature.Metric.UnitType

Temperature.Imperial.Value
Temperature.Imperial.Unit
Temperature.Imperial.UnitType
```

### RealFeelTemperature

```text
RealFeelTemperature.Metric.Value
RealFeelTemperature.Metric.Unit
RealFeelTemperature.Metric.UnitType

RealFeelTemperature.Imperial.Value
RealFeelTemperature.Imperial.Unit
RealFeelTemperature.Imperial.UnitType
```

### Wind

```text
Wind.Direction.Degrees
Wind.Direction.Localized
Wind.Direction.English

Wind.Speed.Metric.Value
Wind.Speed.Metric.Unit
Wind.Speed.Metric.UnitType

Wind.Speed.Imperial.Value
Wind.Speed.Imperial.Unit
Wind.Speed.Imperial.UnitType
```

### WindGust

```text
WindGust.Speed.Metric.*
WindGust.Speed.Imperial.*
```

### 降水总结

```text
PrecipitationSummary.Precipitation
PrecipitationSummary.PastHour
PrecipitationSummary.Past3Hours
PrecipitationSummary.Past6Hours
PrecipitationSummary.Past9Hours
PrecipitationSummary.Past12Hours
PrecipitationSummary.Past18Hours
PrecipitationSummary.Past24Hours
```

每一个时间段对象通常都有：

```text
Metric.Value
Metric.Unit
Metric.UnitType
Imperial.Value
Imperial.Unit
Imperial.UnitType
```

### 温度总结

```text
TemperatureSummary.Past6HourRange
TemperatureSummary.Past12HourRange
TemperatureSummary.Past24HourRange
```

每个范围包含：

```text
Minimum
Maximum
```

每个 Minimum / Maximum 又包含公制和英制温度对象。

### 其他实况字段

完整数据还包括：

```text
UVIndex
UVIndexText
Visibility
ObstructionsToVisibility
CloudCover
Ceiling
Pressure
PressureTendency
Past24HourTemperatureDeparture
ApparentTemperature
WindChillTemperature
WetBulbTemperature
Precip1hr
```

其中：

```text
Visibility
CloudCover
Ceiling
Pressure
```

适合天气看板；

```text
ApparentTemperature
WindChillTemperature
WetBulbTemperature
```

适合体感和专业气象展示。

---

# 5. 逐日天气预报 API

## 5.1 标准时长

当前标准能力：

```text
1day
5day
10day
```

### 1 日

```text
https://openapi.weathercn.com/forecasts/v1/daily/1day/101924.json
```

### 5 日

```text
https://openapi.weathercn.com/forecasts/v1/daily/5day/101924.json
```

### 10 日

```text
https://openapi.weathercn.com/forecasts/v1/daily/10day/101924.json
```

完整请求推荐：

```text
?apikey=YOUR_API_KEY&language=zh-cn&details=true&metric=true
```

---

## 5.2 Python

```python
import requests

location_key = "101924"

url = (
    "https://openapi.weathercn.com/"
    f"forecasts/v1/daily/5day/"
    f"{location_key}.json"
)

params = {
    "apikey": "YOUR_API_KEY",
    "language": "zh-cn",
    "details": "true",
    "metric": "true"
}

response = requests.get(
    url,
    params=params,
    timeout=10
)

response.raise_for_status()

data = response.json()

print(data)
```

---

## 5.3 请求参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| apikey | String | 是 | API Key |
| version | String | 是 | `v1` |
| locationkey | String | 是 | Location Key |
| format | String | 否 | JSON |
| language | String | 否 | 返回语言 |
| details | String | 否 | 完整/简化 |
| metric | String | 否 | 公制单位 |

---

## 5.4 返回结构

顶层：

```text
Headline
DailyForecasts[]
```

### Headline

```text
Headline.EffectiveDate
Headline.EffectiveEpochDate
Headline.Severity
Headline.Text
Headline.Category
Headline.EndDate
Headline.EndEpochDate
Headline.MobileLink
Headline.Link
```

### DailyForecasts

每一天主要包括：

```text
Date
EpochDate
Sun
Moon
Temperature
RealFeelTemperature
RealFeelTemperatureShade
HoursOfSun
DegreeDaySummary
AirAndPollen
Day
Night
Sources
MobileLink
Link
```

---

## 5.5 Sun

```text
Sun.Rise
Sun.EpochRise
Sun.Set
Sun.EpochSet
```

---

## 5.6 Moon

```text
Moon.Rise
Moon.EpochRise
Moon.Set
Moon.EpochSet
Moon.Phase
Moon.Age
```

---

## 5.7 Temperature

```text
Temperature.Minimum
Temperature.Maximum
```

每一项包含：

```text
Value
Unit
UnitType
```

---

## 5.8 RealFeelTemperature

```text
RealFeelTemperature.Minimum
RealFeelTemperature.Maximum
```

---

## 5.9 RealFeelTemperatureShade

```text
RealFeelTemperatureShade.Minimum
RealFeelTemperatureShade.Maximum
```

---

## 5.10 Day 白天数据

主要字段：

```text
Day.Icon
Day.IconPhrase
Day.ShortPhrase
Day.LongPhrase

Day.LocalSource.Id
Day.LocalSource.Name
Day.LocalSource.WeatherCode
Day.LocalSource.WindLevelCode
Day.LocalSource.WindDirectionCode
Day.LocalSource.PubName
Day.LocalSource.PubTime
Day.LocalSource.EpochPubTime

Day.HasPrecipitation
Day.PrecipitationType
Day.PrecipitationIntensity
Day.PrecipitationProbability
Day.ThunderstormProbability
Day.RainProbability
Day.SnowProbability
Day.IceProbability
```

---

## 5.11 Day Wind

```text
Day.Wind.Speed
Day.Wind.Direction
```

方向：

```text
Degrees
Localized
English
```

速度：

```text
Metric.Value
Metric.Unit
Metric.UnitType

Imperial.Value
Imperial.Unit
Imperial.UnitType
```

---

## 5.12 Day WindGust

```text
Day.WindGust.Speed
Day.WindGust.Direction
```

---

## 5.13 Day 降水量

```text
Day.TotalLiquid
Day.Rain
Day.Snow
Day.Ice
```

每项主要：

```text
Value
Unit
UnitType
```

---

## 5.14 Day 其他字段

```text
Day.HoursOfPrecipitation
Day.HoursOfRain
Day.HoursOfSnow
Day.HoursOfIce
Day.CloudCover
Day.Evapotranspiration
Day.SolarIrradiance
```

---

## 5.15 Night 夜间数据

夜间数据结构与 Day 类似，核心包括：

```text
Night.Icon
Night.IconPhrase
Night.ShortPhrase
Night.LongPhrase

Night.LocalSource
Night.HasPrecipitation
Night.PrecipitationType
Night.PrecipitationIntensity
Night.PrecipitationProbability
Night.ThunderstormProbability
Night.RainProbability
Night.SnowProbability
Night.IceProbability

Night.Wind
Night.WindGust

Night.TotalLiquid
Night.Rain
Night.Snow
Night.Ice

Night.HoursOfPrecipitation
Night.HoursOfRain
Night.HoursOfSnow
Night.HoursOfIce
Night.CloudCover
Night.Evapotranspiration
Night.SolarIrradiance
```

---

## 5.16 DegreeDaySummary

用于度日统计，适合需要专业气象统计的应用。

---

## 5.17 AirAndPollen

逐日结果中可以出现：

```text
Name
Value
Category
CategoryValue
Type
```

可用于花粉、空气相关展示。

---

# 6. 逐小时天气预报 API

## 6.1 标准时长

当前标准：

```text
1hour
12hour
24hour
72hour
```

### URL

```text
https://openapi.weathercn.com/forecasts/v1/hourly/{Nhour}/{locationkey}.json
```

例如：

```text
https://openapi.weathercn.com/forecasts/v1/hourly/24hour/101924.json?apikey=YOUR_API_KEY&language=zh-cn&details=true&metric=true
```

---

## 6.2 Python

```python
import requests

url = (
    "https://openapi.weathercn.com/"
    "forecasts/v1/hourly/24hour/101924.json"
)

params = {
    "apikey": "YOUR_API_KEY",
    "language": "zh-cn",
    "details": "true",
    "metric": "true"
}

response = requests.get(
    url,
    params=params,
    timeout=10
)

response.raise_for_status()

data = response.json()

for item in data:
    print(
        item["DateTime"],
        item["IconPhrase"],
        item["Temperature"]["Value"]
    )
```

---

## 6.3 请求参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| apikey | String | 是 | API Key |
| version | String | 是 | `v1` |
| locationkey | String | 是 | Location Key |
| language | String | 否 | 返回语言 |
| details | String | 否 | 完整数据 |
| metric | String | 否 | 公制单位 |

---

## 6.4 返回字段

| 字段 | 类型 | 说明 |
|---|---|---|
| DateTime | String | 预报时间 |
| EpochDateTime | Int | UNIX 时间戳 |
| WeatherIcon | Int | 天气图标 |
| IconPhrase | String | 天气描述 |
| HasPrecipitation | Boolean | 是否降水 |
| IsDaylight | Boolean | 是否白天 |
| Temperature | Object | 温度 |
| LocalSource | Object | 本地数据源 |
| PrecipitationProbability | Int | 降水概率 |
| MobileLink | String | 移动链接 |
| Link | String | 网页链接 |

LocalSource：

```text
Id
Name
WeatherCode
WindLevelCode
WindDirectionCode
Pressure
```

Temperature：

```text
Value
Unit
UnitType
```

---

# 7. 分钟级降水预报 API

## 7.1 特点

这是标准能力中比较特殊的一个接口：

```text
不需要 Location Key
```

直接使用：

```text
纬度,经度
```

查询中国区域未来约 2 小时的短临降水。

---

## 7.2 标准 URL

```http
GET https://openapi.weathercn.com/nowcast_cn/v3/basic
```

示例：

```text
https://openapi.weathercn.com/nowcast_cn/v3/basic?q=39.95,116.328&apikey=YOUR_API_KEY
```

---

## 7.3 参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| apikey | String | 是 | API Key |
| q | String | 是 | `纬度,经度` |

---

## 7.4 Python

```python
import requests

url = "https://openapi.weathercn.com/nowcast_cn/v3/basic"

params = {
    "q": "39.95,116.328",
    "apikey": "YOUR_API_KEY"
}

response = requests.get(
    url,
    params=params,
    timeout=10
)

response.raise_for_status()

data = response.json()

print(data)
```

---

## 7.5 返回字段

顶层：

```text
Status
Msg
Lat
Lon
Data
```

Data：

```text
Data.IfPre
Data.IsLocalPre
Data.PreTypeCode
Data.PreType
Data.NearestPreDirection
Data.NearestPre
Data.Intensity
Data.Interval
Data.Description
Data.ShortPhrase
Data.Datetime
Data.Epochtime
Data.MobileLink
Data.CurrentConditions
```

另外可以存在：

```text
Data.HourlyForecastsNext2H
```

---

## 7.6 Intensity 的理解

`Intensity` 是降水强度序列。

官方说明：

```text
每 6 分钟一个值
```

配合：

```text
Interval
```

可以画出：

```text
未来约 2 小时降水趋势图
```

适合：

```text
是否需要带伞
实时降雨动画
短临预警
```

---

# 8. 天气灾害预警 API

## 8.1 标准 URL

```http
GET https://openapi.weathercn.com/alerts/v1/{locationkey}.json
```

示例：

```text
https://openapi.weathercn.com/alerts/v1/101924.json?apikey=YOUR_API_KEY&language=zh-cn&details=true
```

---

## 8.2 Python

```python
import requests

url = (
    "https://openapi.weathercn.com/"
    "alerts/v1/101924.json"
)

params = {
    "apikey": "YOUR_API_KEY",
    "language": "zh-cn",
    "details": "true"
}

response = requests.get(
    url,
    params=params,
    timeout=10
)

response.raise_for_status()

data = response.json()

if not data:
    print("当前没有生效预警")
else:
    for alert in data:
        print(
            alert["Type"],
            alert["Level"],
            alert["AlarmLevel"]
        )
```

---

## 8.3 参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| apikey | String | 是 | API Key |
| version | String | 是 | `v1` |
| locationkey | String | 是 | Location Key |
| format | String | 否 | JSON |
| language | String | 否 | 返回语言 |
| details | String | 否 | 完整数据 |

---

## 8.4 返回字段

预警接口返回的是：

```text
Array
```

每个预警对象主要包括：

```text
CountryCode
AlertID
Description
Category
Priority
Type
TypeID
Level
AlarmLevel
Color
Source
SourceId
Area
HaveReadyStatements
MobileLink
Link
```

Description：

```text
Description.Localized
Description.English
```

Color：

```text
Color.Name
Color.Red
Color.Green
Color.Blue
Color.Hex
```

Area：

```text
Area[].Name
Area[].StartTime
Area[].EpochStartTime
Area[].EndTime
Area[].EpochEndTime
Area[].LastAction
Area[].Text
Area[].LanguageCode
Area[].Summary
```

LastAction：

```text
LastAction.Localized
LastAction.English
```

---

## 8.5 无预警时

非常重要：

```json
[]
```

代表：

```text
HTTP 200
请求成功
当前没有生效预警
```

不要把空数组当成 API 错误。

---

# 9. 生活指数 API

## 9.1 标准能力

当前标准能力：

```text
1day
```

指数组：

```text
100
```

官方当前示例：

```text
https://openapi.weathercn.com/indices/v1/daily/1day/101924/100?apikey=YOUR_API_KEY&language=zh-cn&details=true
```

---

## 9.2 参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| apikey | String | 是 | API Key |
| version | String | 是 | `v1` |
| locationkey | String | 是 | Location Key |
| format | String | 否 | JSON |
| language | String | 否 | 返回语言 |
| details | String | 否 | 完整数据 |

路径中的：

```text
100
```

表示国内常用生活指数组。

---

## 9.3 Python

```python
import requests

url = (
    "https://openapi.weathercn.com/"
    "indices/v1/daily/1day/101924/100"
)

params = {
    "apikey": "YOUR_API_KEY",
    "language": "zh-cn",
    "details": "true"
}

response = requests.get(
    url,
    params=params,
    timeout=10
)

response.raise_for_status()

data = response.json()

for item in data:
    print(
        item["Name"],
        item["Category"]
    )
```

---

## 9.4 返回字段

| 字段 | 类型 | 说明 |
|---|---|---|
| Name | String | 指数名称 |
| ID | Int | 指数 ID |
| Ascending | Boolean | 是否数值越大越好 |
| LocalDateTime | String | 本地有效时间 |
| EpochDateTime | Int | UNIX 时间戳 |
| Value | Float | 指数数值 |
| Category | String | 等级描述 |
| CategoryValue | Int | 分类索引 |
| MobileLink | String | 移动链接 |
| Link | String | 网页链接 |

常见生活指数：

```text
穿衣
洗车
运动
旅游
感冒
紫外线
晨练
```

具体指数 ID 与含义以官方“指数列表”为准。

---

# 10. 空气质量 API

## 10.1 标准接口

```http
GET https://openapi.weathercn.com/airquality/v1/global/observations/{locationkey}.json
```

北京示例：

```text
https://openapi.weathercn.com/airquality/v1/global/observations/101924.json?apikey=YOUR_API_KEY&language=zh-cn
```

---

## 10.2 Python

```python
import requests

url = (
    "https://openapi.weathercn.com/"
    "airquality/v1/global/observations/101924.json"
)

params = {
    "apikey": "YOUR_API_KEY",
    "language": "zh-cn"
}

response = requests.get(
    url,
    params=params,
    timeout=10
)

response.raise_for_status()

data = response.json()

print(data)
```

---

## 10.3 请求参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| apikey | String | 是 | API Key |
| version | String | 是 | `v1` |
| locationkey | String | 是 | Location Key |
| format | String | 否 | JSON |
| language | String | 否 | 返回语言 |
| details | String | 否 | 完整/简化 |

---

## 10.4 返回字段

| 字段 | 类型 | 单位/说明 |
|---|---|---|
| CarbonMonoxide | Float | CO，mg/m³ |
| ParticulateMatter2_5 | Float | PM2.5，μg/m³ |
| NitrogenMonoxide | Float | NO |
| EpochDate | Int | UNIX 时间戳 |
| Lead | Float | 铅，μg/m³ |
| Ozone | Float | O₃，μg/m³ |
| Index | Int | AQI |
| ParticulateMatter10 | Float | PM10，μg/m³ |
| SulfurDioxide | Float | SO₂，μg/m³ |
| Date | String | 本地观测时间 |
| NitrogenDioxide | Float | NO₂，μg/m³ |
| Source | String | 数据来源 |

---

# 11. Python 调用统一封装

建议把 API Key、请求超时、异常处理统一处理。

```python
import os
import requests


class WeatherClient:

    BASE_URL = "https://openapi.weathercn.com"

    def __init__(self):
        self.api_key = os.getenv("WEATHER_API_KEY")

        if not self.api_key:
            raise RuntimeError(
                "WEATHER_API_KEY 未设置"
            )

    def get(self, path, params=None):

        params = params or {}

        params["apikey"] = self.api_key

        response = requests.get(
            self.BASE_URL + path,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        return response.json()

    def search_city(self, city):

        return self.get(
            "/locations/v1/cities/translate",
            {
                "q": city,
                "language": "zh-cn",
                "details": "true"
            }
        )

    def current_weather(self, location_key):

        return self.get(
            f"/currentconditions/v1/{location_key}.json",
            {
                "language": "zh-cn",
                "details": "true"
            }
        )

    def daily_forecast(
        self,
        location_key,
        days="5day"
    ):

        return self.get(
            f"/forecasts/v1/daily/"
            f"{days}/{location_key}.json",
            {
                "language": "zh-cn",
                "details": "true",
                "metric": "true"
            }
        )

    def hourly_forecast(
        self,
        location_key,
        hours="24hour"
    ):

        return self.get(
            f"/forecasts/v1/hourly/"
            f"{hours}/{location_key}.json",
            {
                "language": "zh-cn",
                "details": "true",
                "metric": "true"
            }
        )

    def alerts(self, location_key):

        return self.get(
            f"/alerts/v1/"
            f"{location_key}.json",
            {
                "language": "zh-cn",
                "details": "true"
            }
        )

    def air_quality(self, location_key):

        return self.get(
            f"/airquality/v1/global/"
            f"observations/{location_key}.json",
            {
                "language": "zh-cn"
            }
        )
```

---

# 12. 最推荐的天气 App 调用流程

如果做网页版天气 App，推荐：

```text
浏览器
  │
  │ 输入：北京
  ↓
Flask / FastAPI
  │
  │ requests
  ↓
定位 API
  │
  ↓
Location Key = 101924
  │
  ├───────────────┐
  ↓               ↓
实况            逐日
  │               │
  ├──────┐        ├──────┐
  ↓      ↓        ↓      ↓
预警   AQI      逐小时  生活指数
```

分钟级降水则：

```text
浏览器 GPS
   ↓
纬度/经度
   ↓
分钟级降水 API
```

---

# 13. 一个完整天气主页需要哪些 API

推荐网页首页组合：

```text
① 定位
   ↓
城市名称 → Location Key

② 实况
   ↓
当前温度
天气
体感
湿度
风速
风向
气压
UV
能见度

③ 逐日
   ↓
未来 5～10 天
最低温
最高温
天气
降水概率
风

④ 逐小时
   ↓
未来 24 小时
温度曲线
降水概率
天气变化

⑤ 分钟级降水
   ↓
未来约 2 小时
是否下雨
降水趋势

⑥ 空气质量
   ↓
AQI
PM2.5
PM10
O₃
NO₂
SO₂
CO

⑦ 预警
   ↓
蓝 / 黄 / 橙 / 红

⑧ 生活指数
   ↓
穿衣
洗车
运动
旅游
紫外线
```

---

# 14. 不属于标准能力的接口

根据当前官网文档，下列页面虽然出现在 API-DOC 总览中，但目前属于进阶/订阅能力，不应当按照标准测试 Key 来理解：

## 14.1 天文数据

包含：

```text
天文实况
天文逐日
天文逐小时
```

官方当前文档标注为进阶订阅能力，标准测试 Key 无法调用。

---

## 14.2 台风数据

包含：

```text
单台风详情
最近 10 条台风列表
按年度查询台风列表
```

目前官方文档标注为进阶订阅能力。

---

## 14.3 天气视频

目前官方产品页面标注：

```text
朝闻天下
新闻联播
```

及其：

```text
视频
封面
标题
时长
分辨率
下载地址
```

属于进阶订阅产品，标准测试 Key 无法调用。

---

# 15. 标准版 API 学习顺序

为了学习 Python `requests`，建议严格按照：

```text
第 1 步
定位搜索
    ↓
GET + params + JSON

第 2 步
实况天气
    ↓
list
    ↓
dict
    ↓
嵌套 JSON

第 3 步
逐小时
    ↓
遍历 list
    ↓
提取字段

第 4 步
逐日
    ↓
复杂嵌套结构

第 5 步
空气质量
    ↓
多个指标

第 6 步
预警
    ↓
判断 [] / 数据

第 7 步
生活指数
    ↓
循环处理

第 8 步
分钟级降水
    ↓
经纬度
    ↓
数组序列

第 9 步
统一 WeatherClient
    ↓
封装 requests

第 10 步
Flask / FastAPI
    ↓
做自己的天气 Web App
```

---

# 16. 最终学习目标

当你学完以后，看到任何一个 API 文档，都应该能够独立完成：

```python
import requests

response = requests.get(
    url,
    params=params,
    timeout=10
)

response.raise_for_status()

data = response.json()
```

然后自己判断：

```text
data 是 list 还是 dict？
        ↓
字段在哪里？
        ↓
是否存在嵌套对象？
        ↓
是否存在数组？
        ↓
是否存在 null？
```

并能够写出：

```python
temperature = data[0]["Temperature"]["Metric"]["Value"]
```

或者：

```python
for item in data:
    print(item["DateTime"])
```

这才是 `requests` 学习的核心。

---

# 17. 官方资料入口

WeatherCN API 文档：

https://platform.weathercn.com/api-doc/overview

定位搜索：

https://platform.weathercn.com/doc/api/location-search.html

实况：

https://platform.weathercn.com/doc/api/current-weather.html

逐日预报：

https://platform.weathercn.com/doc/api/daily-forecast.html

逐小时预报：

https://platform.weathercn.com/doc/api/hourly-forecast.html

分钟级降水：

https://platform.weathercn.com/doc/api/minute-forecast.html

空气质量：

https://platform.weathercn.com/doc/api/air-quality.html

天气预警：

https://platform.weathercn.com/doc/api/weather-alert.html

生活指数：

https://platform.weathercn.com/doc/api/life-index.html

天文：

https://platform.weathercn.com/doc/api/astronomy.html

台风：

https://platform.weathercn.com/doc/api/typhoon.html

天气视频：

https://platform.weathercn.com/doc/api/video-download.html

---

# 18. 注意事项

1. 不要把真实 API Key 写到前端 JavaScript。
2. 不要把真实 API Key 提交到 Git。
3. 推荐使用环境变量保存 Key。
4. 请求统一设置 `timeout`。
5. 使用 `raise_for_status()` 处理 HTTP 错误。
6. JSON 中可能出现 `null`，不要假定每个字段永远有值。
7. `details=true` 会返回更完整的数据，适合学习字段结构。
8. 中国分钟级降水标准接口使用经纬度，不需要 Location Key。
9. 预警接口返回 `[]` 属于正常的“无生效预警”结果。
10. 标准、进阶能力和具体配额可能随官方产品政策调整，开发前应重新确认控制台和官网文档。

---

# 19. 一句话总结

WeatherCN 标准版最值得你掌握的是：

```text
定位
  ↓
Location Key
  ↓
实况
  ↓
逐日
  ↓
逐小时
  ↓
分钟降水

同时：
预警
空气质量
生活指数
```

而对于 Python：

```text
requests
  ↓
HTTP
  ↓
JSON
  ↓
list / dict
  ↓
嵌套字段
  ↓
API 封装
  ↓
Flask / FastAPI
```

这条链掌握以后，你不仅能调用天气 API，GitLab、Zabbix、Grafana、Harbor、CMDB、JumpServer 等 REST API 的调用思路也基本相同。
