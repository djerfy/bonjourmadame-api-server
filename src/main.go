package main

import (
	"fmt"
	"io"
	"log"
	"math/rand"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/PuerkitoBio/goquery"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

var bjrURL = "https://www.bonjourmadame.fr/"

func randInt(max int) int {
	return rand.Intn(max)
}

func randomDate() time.Time {
	start, _ := time.Parse("2006-01-02", "2018-12-10")
	end := time.Now()
	delta := end.Sub(start)
	randomSeconds := randInt(int(delta.Seconds()))
	return start.Add(time.Duration(randomSeconds) * time.Second)
}

func formatDate(date time.Time) string {
	return date.Format("2006-01-02")
}

func formatURI(date time.Time) string {
	return fmt.Sprintf("%d/%02d/%02d/", date.Year(), date.Month(), date.Day())
}

func todayURL() string {
	return bjrURL + formatURI(time.Now())
}

func randomURL() string {
	return bjrURL + formatURI(randomDate())
}

func urljoin(base, target string) string {
	baseURL, err := url.Parse(base)
	if err != nil {
		return ""
	}

	targetURL, err := url.Parse(target)
	if err != nil {
		return ""
	}

	resolvedURL := baseURL.ResolveReference(targetURL)

	return resolvedURL.String()
}

func parseHTML(body string) map[string]interface{} {
	doc, err := goquery.NewDocumentFromReader(strings.NewReader(body))
	if err != nil {
		log.Fatal(err)
	}

	result := make(map[string]interface{})

	if img := doc.Find("div.post-content img.alignnone"); img.Length() > 0 {
		if imgUrl, exists := img.Attr("src"); exists {
			tmp := urljoin(imgUrl, imgUrl)
			result["imgUrl"] = strings.Split(tmp, "?")[0]
		}
	}

	if title := doc.Find("h1.post-title a"); title.Length() > 0 {
		result["title"] = title.Text()
	}

	if content := doc.Find("div.post-content a"); content.Length() > 0 {
		if href, exists := content.Attr("href"); exists && href == "https://fr.tipeee.com/bonjour-madame-soutien-et-amour-de-la-madame" {
			result["tipee"] = true
		} else {
			result["tipee"] = false
		}
	}

	return result
}

func getURL(action string) (string, int, string) {
	var pictureURL string
	var pageTitle string
	retriesNow := 0
	retriesMax := 9

	if value, exists := os.LookupEnv("RETRIES_MAX"); exists {
		retriesMax, _ = strconv.Atoi(value)
	}

	for pictureURL == "" && !strings.HasSuffix(pictureURL, "noclub.png") && retriesNow <= retriesMax {
		var url string
		if action == "random" {
			url = randomURL()
		} else if action == "today" {
			url = todayURL()
		}

		response, err := http.Get(url)
		if err != nil || response.StatusCode != 200 {
			retriesNow++
			continue
		}

		body, err := io.ReadAll(response.Body)
		if err != nil {
			log.Fatal(err)
		}

		p := parseHTML(string(body))
		pictureURL = p["imgUrl"].(string)
		pageTitle = p["title"].(string)

		if p["tipee"].(bool) {
			retriesNow++
			continue
		}

		break
	}

	if pictureURL == "" || strings.HasSuffix(pictureURL, "noclub.png") {
		return "", retriesNow, ""
	}

	return pictureURL, retriesNow, pageTitle
}

func defineHostname() string {
	hostname, exists := os.LookupEnv("HOSTNAME")
	if !exists {
		hostname = uuid.New().String()
	}

	return hostname
}

func defineVersion() string {
	version, exists := os.LookupEnv("VERSION")
	if !exists {
		version = "0.0.0"
	}

	return version
}

func LoggerFormatter(p gin.LogFormatterParams) string {
	return fmt.Sprintf("%s - [%s] \"%s %s %s %d %s \"%s\" %s\"\n",
		p.ClientIP,
		p.TimeStamp.Format(time.RFC1123),
		p.Method,
		p.Path,
		p.Request.Proto,
		p.StatusCode,
		p.Latency,
		p.Request.UserAgent(),
		p.ErrorMessage,
	)
}

func healthHandler(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"status": "healthy"})
}

func indexHandler(c *gin.Context) {
	c.HTML(http.StatusOK, "index.html", gin.H{"version": defineVersion()})
}

func pingHandler(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"response": "pong"})
}

func versionHandler(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"response": defineVersion()})
}

func latestHandler(c *gin.Context) {
	url, retry, title := getURL("today")
	c.JSON(http.StatusOK, gin.H{
		"node":        defineHostname(),
		"description": "Return latest picture URL",
		"url":         url,
		"title":       title,
		"retry":       retry,
	})
}

func randomHandler(c *gin.Context) {
	url, retry, title := getURL("random")
	c.JSON(http.StatusOK, gin.H{
		"node":        defineHostname(),
		"description": "Return random picture URL",
		"url":         url,
		"title":       title,
		"retry":       retry,
	})
}

func main() {
	r := gin.Default()

	r.Static("/static", "./static")
	r.LoadHTMLGlob("./templates/*.html")

	r.GET("/", indexHandler)
	r.GET("/api/ping", pingHandler)
	r.GET("/api/health", healthHandler)
	r.GET("/api/version", versionHandler)
	r.GET("/api/latest", latestHandler)
	r.GET("/api/random", randomHandler)

	r.Run()
}
