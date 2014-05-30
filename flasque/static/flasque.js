var flasqueApp = angular.module("flasqueApp", ['ngRoute']);
flasqueApp.config(function($routeProvider) {
    $routeProvider
        .when("/", {
            templateUrl: "/static/queues.html",
            controller: "queueController",
            activetab: 'queues',
        })
        .when("/channels", {
            templateUrl: "/static/channels.html",
            controller: "channelController",
            activetab: "channels",
        });
});

flasqueApp.controller('queueController', function($scope, $route) {
    $scope.$route = $route;
    $scope.queues = {};
    var sse = new EventSource("/status");
    sse.onmessage = function(message){
        if (message.data){
            var data = angular.fromJson(message.data);
            for (e in data) {
                $scope.queues[data[e][0]] = {
                    waiting: data[e][1],
                    pending: data[e][2],
                    done: data[e][3],
                }
            }
            $scope.$apply();
        }
    };
});

flasqueApp.controller('channelController', function($scope, $route) {
    $scope.$route = $route;
    $scope.messages = [];
    var sse = new EventSource("/channel/");
    sse.onmessage = function(message){
        if (message.data){
            var msg = angular.fromJson(message.data);
            $scope.messages.push(msg);
            $scope.messages = $scope.messages.slice(-30)
            $scope.$apply();
        }
    };
});
