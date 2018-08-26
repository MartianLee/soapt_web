Rails.application.routes.draw do
  # For details on the DSL available within this file, see http://guides.rubyonrails.org/routing.html
  root 'home#index'
  get '/analyzed', to: "home#analyzed", as: 'analyzed'
  get '/test', to: "home#test", as: 'test'
  get '/about', to: "home#about", as: "about"
end
