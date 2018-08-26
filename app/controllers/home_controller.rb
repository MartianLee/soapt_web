class HomeController < ApplicationController

  def index
  end
  def analyzed
    if params[:id].nil? or !params[:id].include?('@')
      redirect_to root_path
      flash[:notice] = "ID를 정확히 입력해 주세요!"
      return
    end

    UserTweet.destroy_all()
    Result.destroy_all()
    flash[:notice] = "Loading Tweets..."
    begin
      callPython = fork {
        exec("python3 crawling_user.py " + params[:id])
      }
      callAnaylzed = fork {
        exec("python3 analyze_user_timeline.py")
      }
    rescue Timeout::Error
      Process.kill callPython
      Process.kill callAnaylzed
    end
    Process.wait callPython
    Process.wait callAnaylzed

    @labels= ['기쁨', '슬픔', '화남', '즐거움', '무서움']
    @radarData = {
      labels: @labels,
      datasets: [
        {
          label: "감정 분석",
          backgroundColor: "rgba(#{rand(255)},#{rand(255)},#{rand(255)},0.2)",
          data: [],
          pointRadius: 6,
          pointBorderWidth: 3,
          radius: 5
        }
      ]
    }
    @options = {
      scale: {
        ticks: {
          beginAtZero: true,
          min: 0,
          max: 100,
          stepSize: 20
        },
        pointLabels: {
          fontSize: 18
        }
      },
      width: '200px',
      height: '200px'
    }
    @results = Result.all()
    @tweets = UserTweet.all()
  end

  def test
    @sentiments = Result.new
    @sentiments.tweet_text = UserTweet.first.tweet_text if UserTweet.first.present?
    @sentiments.sentiment1 = 87
    @sentiments.sentiment2 = 59
    @sentiments.sentiment3 = 73
    @sentiments.sentiment4 = 43
    @sentiments.sentiment5 = 67

    @labels= ['기쁨', '슬픔', '화남', '즐거움', '무서움']
    @radarData = {
      labels: @labels,
      datasets: [
        {
          label: "감정 분석",
          backgroundColor: "rgba(#{rand(255)},#{rand(255)},#{rand(255)},0.2)",
          data: [],
          pointRadius: 6,
          pointBorderWidth: 3,
          radius: 5
        }
      ]
    }
    @options = {
      scale: {
        ticks: {
          beginAtZero: true,
          min: 0,
          max: 100,
          stepSize: 20
        },
        pointLabels: {
          fontSize: 18
        }
      },
      width: '200px',
      height: '200px'
    }
    @tweets = UserTweet.all()
    @results = UserTweet.all()
  end
end
